"""SQLite persistence for the control plane.

One file, one connection, guarded by a lock. Tasks survive a restart, which is
what makes checkpoints and recovery possible.

SQLite is deliberate for the prototype: no server to run, no extra moving
parts. The store is the only place that knows about SQL, so swapping in
PostgreSQL later means rewriting this module and nothing else.
"""

import sqlite3
import threading
import time
from pathlib import Path

from assistant.control.models import (
    ActivityEvent,
    Approval,
    ApprovalStatus,
    Device,
    DeviceStatus,
    EventType,
    Helper,
    HelperStatus,
    Permission,
    PermissionStatus,
    StepStatus,
    Task,
    TaskStatus,
    TaskStep,
    dumps,
    loads,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    platform TEXT,
    status TEXT NOT NULL,
    last_seen REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS helpers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    framework TEXT NOT NULL,
    device_id TEXT,
    status TEXT NOT NULL,
    capabilities TEXT NOT NULL,
    current_task_id TEXT,
    last_active REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    goal TEXT NOT NULL,
    status TEXT NOT NULL,
    helper_id TEXT,
    device_id TEXT,
    summary TEXT,
    checkpoint TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS task_steps (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    position INTEGER NOT NULL,
    label TEXT NOT NULL,
    status TEXT NOT NULL,
    detail TEXT,
    FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS permissions (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    resource TEXT NOT NULL,
    actions TEXT NOT NULL,
    device_id TEXT,
    status TEXT NOT NULL,
    granted_at REAL NOT NULL,
    expires_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS approvals (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    action TEXT NOT NULL,
    question TEXT NOT NULL,
    reason TEXT,
    impact TEXT,
    status TEXT NOT NULL,
    created_at REAL NOT NULL,
    resolved_at REAL
);

CREATE TABLE IF NOT EXISTS activity_events (
    id TEXT PRIMARY KEY,
    task_id TEXT,
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    actor TEXT,
    device_id TEXT,
    timestamp REAL NOT NULL,
    metadata TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_steps_task ON task_steps (task_id, position);
CREATE INDEX IF NOT EXISTS idx_events_time ON activity_events (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_task ON activity_events (task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_approvals_status ON approvals (status, created_at DESC);
"""

# Ordered, named migrations. Every schema change goes here rather than into
# SCHEMA, so an existing data/control.db is upgraded in place instead of
# silently missing columns. Names are permanent; never renumber or reorder.
MIGRATIONS = [
    ("0001_baseline", SCHEMA),
    ("0002_device_pairing", [
        ("devices", "token_hash", "ALTER TABLE devices ADD COLUMN token_hash TEXT"),
        ("devices", "paired_at", "ALTER TABLE devices ADD COLUMN paired_at REAL"),
    ]),
]

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "control.db"


class ControlStore:
    """Thread-safe SQLite storage for control-plane records."""

    def __init__(self, db_path=None):
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # check_same_thread=False because worker threads share this connection;
        # every access is serialised through _lock.
        self._connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._lock = threading.RLock()

        with self._lock:
            self._migrate()

    def close(self):
        with self._lock:
            self._connection.close()

    # -- migrations ---------------------------------------------------------

    def _migrate(self):
        """Bring the database up to date, one named migration at a time.

        A migration is either a SQL script or a list of column additions,
        each guarded by the column it adds so re-running is harmless.
        """
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS schema_version ("
            "  name TEXT PRIMARY KEY,"
            "  applied_at REAL NOT NULL"
            ")")

        applied = {row["name"] for row in
                   self._connection.execute("SELECT name FROM schema_version")}

        for name, migration in MIGRATIONS:
            if name in applied:
                continue

            if isinstance(migration, str):
                self._connection.executescript(migration)
            else:
                for table, column, statement in migration:
                    if not self._has_column(table, column):
                        self._connection.execute(statement)

            self._connection.execute(
                "INSERT INTO schema_version (name, applied_at) VALUES (?, ?)",
                (name, time.time()))

        self._connection.commit()

    def _has_column(self, table, column):
        rows = self._connection.execute(f"PRAGMA table_info({table})").fetchall()
        return any(row["name"] == column for row in rows)

    def schema_versions(self):
        """Migrations applied to this database, oldest first."""
        return [row["name"] for row in
                self._rows("SELECT name FROM schema_version ORDER BY applied_at")]

    # -- low level ----------------------------------------------------------

    def _write(self, sql, params=()):
        with self._lock:
            cursor = self._connection.execute(sql, params)
            self._connection.commit()
            return cursor

    def _rows(self, sql, params=()):
        with self._lock:
            return self._connection.execute(sql, params).fetchall()

    def _row(self, sql, params=()):
        with self._lock:
            return self._connection.execute(sql, params).fetchone()

    # -- devices ------------------------------------------------------------

    def save_device(self, device):
        self._write(
            "INSERT INTO devices (id, name, kind, platform, status, last_seen, "
            "token_hash, paired_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET name=excluded.name, kind=excluded.kind, "
            "platform=excluded.platform, status=excluded.status, "
            "last_seen=excluded.last_seen, token_hash=excluded.token_hash, "
            "paired_at=excluded.paired_at",
            (device.id, device.name, device.kind, device.platform,
             device.status.value, device.last_seen, device.token_hash,
             device.paired_at),
        )
        return device

    def get_device_by_token(self, token_hash):
        """Look a device up by the hash of its token. Never by the token itself."""
        if not token_hash:
            return None
        return _to_device(self._row("SELECT * FROM devices WHERE token_hash = ?",
                                    (token_hash,)))

    def get_device(self, device_id):
        row = self._row("SELECT * FROM devices WHERE id = ?", (device_id,))
        return _to_device(row)

    def list_devices(self):
        return [_to_device(row) for row in self._rows("SELECT * FROM devices ORDER BY name")]

    # -- helpers ------------------------------------------------------------

    def save_helper(self, helper):
        self._write(
            "INSERT INTO helpers (id, name, framework, device_id, status, capabilities, "
            "current_task_id, last_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET name=excluded.name, framework=excluded.framework, "
            "device_id=excluded.device_id, status=excluded.status, "
            "capabilities=excluded.capabilities, current_task_id=excluded.current_task_id, "
            "last_active=excluded.last_active",
            (helper.id, helper.name, helper.framework, helper.device_id,
             helper.status.value, dumps(helper.capabilities),
             helper.current_task_id, helper.last_active),
        )
        return helper

    def get_helper(self, helper_id):
        return _to_helper(self._row("SELECT * FROM helpers WHERE id = ?", (helper_id,)))

    def list_helpers(self):
        return [_to_helper(row) for row in self._rows("SELECT * FROM helpers ORDER BY name")]

    # -- tasks --------------------------------------------------------------

    def save_task(self, task):
        self._write(
            "INSERT INTO tasks (id, goal, status, helper_id, device_id, summary, "
            "checkpoint, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET goal=excluded.goal, status=excluded.status, "
            "helper_id=excluded.helper_id, device_id=excluded.device_id, "
            "summary=excluded.summary, checkpoint=excluded.checkpoint, "
            "updated_at=excluded.updated_at",
            (task.id, task.goal, task.status.value, task.helper_id, task.device_id,
             task.summary, dumps(task.checkpoint), task.created_at, task.updated_at),
        )
        return task

    def get_task(self, task_id):
        return _to_task(self._row("SELECT * FROM tasks WHERE id = ?", (task_id,)))

    def list_tasks(self, limit=50, active_only=False):
        sql = "SELECT * FROM tasks"
        params = []
        if active_only:
            active = (TaskStatus.PENDING.value, TaskStatus.RUNNING.value,
                      TaskStatus.WAITING_APPROVAL.value)
            sql += f" WHERE status IN ({','.join('?' * len(active))})"
            params.extend(active)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        return [_to_task(row) for row in self._rows(sql, tuple(params))]

    # -- steps --------------------------------------------------------------

    def save_step(self, step):
        self._write(
            "INSERT INTO task_steps (id, task_id, position, label, status, detail) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET label=excluded.label, "
            "status=excluded.status, detail=excluded.detail",
            (step.id, step.task_id, step.position, step.label,
             step.status.value, step.detail),
        )
        return step

    def get_step(self, step_id):
        return _to_step(self._row("SELECT * FROM task_steps WHERE id = ?", (step_id,)))

    def list_steps(self, task_id):
        return [_to_step(row) for row in self._rows(
            "SELECT * FROM task_steps WHERE task_id = ? ORDER BY position", (task_id,))]

    # -- permissions --------------------------------------------------------

    def save_permission(self, permission):
        self._write(
            "INSERT INTO permissions (id, task_id, resource, actions, device_id, "
            "status, granted_at, expires_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET status=excluded.status, "
            "expires_at=excluded.expires_at",
            (permission.id, permission.task_id, permission.resource,
             dumps(permission.actions), permission.device_id,
             permission.status.value, permission.granted_at, permission.expires_at),
        )
        return permission

    def get_permission(self, permission_id):
        return _to_permission(
            self._row("SELECT * FROM permissions WHERE id = ?", (permission_id,)))

    def list_permissions(self, active_only=False, task_id=None):
        sql = "SELECT * FROM permissions"
        clauses, params = [], []
        if active_only:
            clauses.append("status = ?")
            params.append(PermissionStatus.ACTIVE.value)
        if task_id:
            clauses.append("task_id = ?")
            params.append(task_id)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY granted_at DESC"
        return [_to_permission(row) for row in self._rows(sql, tuple(params))]

    # -- approvals ----------------------------------------------------------

    def save_approval(self, approval):
        self._write(
            "INSERT INTO approvals (id, task_id, action, question, reason, impact, "
            "status, created_at, resolved_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET status=excluded.status, "
            "resolved_at=excluded.resolved_at",
            (approval.id, approval.task_id, approval.action, approval.question,
             approval.reason, approval.impact, approval.status.value,
             approval.created_at, approval.resolved_at),
        )
        return approval

    def get_approval(self, approval_id):
        return _to_approval(
            self._row("SELECT * FROM approvals WHERE id = ?", (approval_id,)))

    def list_approvals(self, pending_only=False):
        sql = "SELECT * FROM approvals"
        params = ()
        if pending_only:
            sql += " WHERE status = ?"
            params = (ApprovalStatus.PENDING.value,)
        sql += " ORDER BY created_at DESC"
        return [_to_approval(row) for row in self._rows(sql, params)]

    # -- activity -----------------------------------------------------------

    def save_event(self, event):
        self._write(
            "INSERT INTO activity_events (id, task_id, type, message, actor, "
            "device_id, timestamp, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (event.id, event.task_id, event.type.value, event.message, event.actor,
             event.device_id, event.timestamp, dumps(event.metadata)),
        )
        return event

    def list_events(self, limit=100, task_id=None):
        sql = "SELECT * FROM activity_events"
        params = []
        if task_id:
            sql += " WHERE task_id = ?"
            params.append(task_id)
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        return [_to_event(row) for row in self._rows(sql, tuple(params))]


# -- row -> dataclass -------------------------------------------------------

def _to_device(row):
    if row is None:
        return None
    keys = row.keys()
    return Device(id=row["id"], name=row["name"], kind=row["kind"],
                  platform=row["platform"] or "",
                  status=DeviceStatus(row["status"]), last_seen=row["last_seen"],
                  token_hash=(row["token_hash"] or "") if "token_hash" in keys else "",
                  paired_at=(row["paired_at"] or 0.0) if "paired_at" in keys else 0.0)


def _to_helper(row):
    if row is None:
        return None
    return Helper(id=row["id"], name=row["name"], framework=row["framework"],
                  device_id=row["device_id"] or "",
                  status=HelperStatus(row["status"]),
                  capabilities=loads(row["capabilities"], []),
                  current_task_id=row["current_task_id"] or "",
                  last_active=row["last_active"])


def _to_task(row):
    if row is None:
        return None
    return Task(id=row["id"], goal=row["goal"], status=TaskStatus(row["status"]),
                helper_id=row["helper_id"] or "", device_id=row["device_id"] or "",
                summary=row["summary"] or "", checkpoint=loads(row["checkpoint"], {}),
                created_at=row["created_at"], updated_at=row["updated_at"])


def _to_step(row):
    if row is None:
        return None
    return TaskStep(id=row["id"], task_id=row["task_id"], position=row["position"],
                    label=row["label"], status=StepStatus(row["status"]),
                    detail=row["detail"] or "")


def _to_permission(row):
    if row is None:
        return None
    return Permission(id=row["id"], task_id=row["task_id"] or "",
                      resource=row["resource"], actions=loads(row["actions"], []),
                      device_id=row["device_id"] or "",
                      status=PermissionStatus(row["status"]),
                      granted_at=row["granted_at"], expires_at=row["expires_at"])


def _to_approval(row):
    if row is None:
        return None
    return Approval(id=row["id"], task_id=row["task_id"] or "", action=row["action"],
                    question=row["question"], reason=row["reason"] or "",
                    impact=row["impact"] or "", status=ApprovalStatus(row["status"]),
                    created_at=row["created_at"], resolved_at=row["resolved_at"] or 0.0)


def _to_event(row):
    if row is None:
        return None
    return ActivityEvent(id=row["id"], task_id=row["task_id"] or "",
                         type=EventType(row["type"]), message=row["message"],
                         actor=row["actor"] or "JARVIS",
                         device_id=row["device_id"] or "",
                         timestamp=row["timestamp"],
                         metadata=loads(row["metadata"], {}))
