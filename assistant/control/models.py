"""Data model for the JARVIS control plane.

These are the concepts the whole system coordinates around: the user's goals
(Task) broken into observable steps (TaskStep), the machines and AI helpers
that carry them out (Device, Helper), the access those helpers are granted
(Permission), the decisions the user must make (Approval), and the readable
record of what happened (ActivityEvent).

The types are plain dataclasses so they can cross any boundary - SQLite rows,
JSON for the desktop and mobile clients, or the in-process event bus - without
dragging a framework along with them.
"""

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum


def new_id():
    return uuid.uuid4().hex


def now():
    return time.time()


class TaskStatus(str, Enum):
    PENDING = "pending"          # accepted, not started
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self):
        return self in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)


class StepStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    EXPIRED = "expired"


class PermissionStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"


class HelperStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    OFFLINE = "offline"
    QUARANTINED = "quarantined"


class EventType(str, Enum):
    """Observable actions only. Never model reasoning."""
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    STEP_STARTED = "step_started"
    STEP_FINISHED = "step_finished"
    HELPER_SELECTED = "helper_selected"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_RESOLVED = "approval_resolved"
    EMERGENCY_STOP = "emergency_stop"
    NOTE = "note"


@dataclass
class Device:
    """A machine JARVIS can work on."""
    id: str = field(default_factory=new_id)
    name: str = ""
    kind: str = "computer"          # computer, phone, server, nas, cloud
    platform: str = ""              # windows, darwin, linux, android, ios
    status: DeviceStatus = DeviceStatus.ONLINE
    last_seen: float = field(default_factory=now)
    token_hash: str = ""            # sha256 of the device's API token
    paired_at: float = 0.0

    @property
    def is_paired(self):
        return bool(self.token_hash)

    def to_dict(self):
        data = _serialise(self)
        # A device's credential never leaves the backend, not even hashed.
        data.pop("token_hash", None)
        return data


@dataclass
class Helper:
    """An AI helper. 'Framework' is an implementation detail the UI hides."""
    id: str = field(default_factory=new_id)
    name: str = ""
    framework: str = "native"       # native, openclaw, langgraph, crewai, mcp
    device_id: str = ""
    status: HelperStatus = HelperStatus.IDLE
    capabilities: list = field(default_factory=list)
    current_task_id: str = ""
    last_active: float = field(default_factory=now)

    def can(self, capability):
        return capability in self.capabilities

    def to_dict(self):
        return _serialise(self)


@dataclass
class TaskStep:
    """One observable step, phrased for a person: 'Finding relevant files'."""
    id: str = field(default_factory=new_id)
    task_id: str = ""
    position: int = 0
    label: str = ""
    status: StepStatus = StepStatus.PENDING
    detail: str = ""

    def to_dict(self):
        return _serialise(self)


@dataclass
class Task:
    """A goal the user asked for, in their own words."""
    id: str = field(default_factory=new_id)
    goal: str = ""
    status: TaskStatus = TaskStatus.PENDING
    helper_id: str = ""
    device_id: str = ""
    summary: str = ""               # plain-language outcome once finished
    checkpoint: dict = field(default_factory=dict)
    created_at: float = field(default_factory=now)
    updated_at: float = field(default_factory=now)

    def to_dict(self):
        return _serialise(self)


@dataclass
class Permission:
    """Task-scoped, time-limited access. Least privilege by construction."""
    id: str = field(default_factory=new_id)
    task_id: str = ""
    resource: str = ""
    actions: list = field(default_factory=list)   # read, write, execute
    device_id: str = ""
    status: PermissionStatus = PermissionStatus.ACTIVE
    granted_at: float = field(default_factory=now)
    expires_at: float = 0.0

    def is_valid(self, at=None):
        at = at if at is not None else now()
        return self.status == PermissionStatus.ACTIVE and at < self.expires_at

    def allows(self, action, at=None):
        return self.is_valid(at) and action in self.actions

    def to_dict(self):
        data = _serialise(self)
        data["seconds_remaining"] = max(0, int(self.expires_at - now()))
        return data


@dataclass
class Approval:
    """A consequential action held until the user decides."""
    id: str = field(default_factory=new_id)
    task_id: str = ""
    action: str = ""                # short label: "Send email"
    question: str = ""              # what JARVIS is about to do
    reason: str = ""                # why
    impact: str = ""                # what changes
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: float = field(default_factory=now)
    resolved_at: float = 0.0

    def to_dict(self):
        return _serialise(self)


@dataclass
class ActivityEvent:
    """One line of the unified timeline, written in plain English."""
    id: str = field(default_factory=new_id)
    task_id: str = ""
    type: EventType = EventType.NOTE
    message: str = ""
    actor: str = "JARVIS"
    device_id: str = ""
    timestamp: float = field(default_factory=now)
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        return _serialise(self)


def _serialise(item):
    """dataclass -> JSON-safe dict, with enums flattened to their values."""
    data = asdict(item)
    for key, value in data.items():
        if isinstance(value, Enum):
            data[key] = value.value
    return data


# -- SQLite helpers ---------------------------------------------------------
# Lists and dicts are stored as JSON text; these keep that in one place.

def dumps(value):
    return json.dumps(value or ([] if isinstance(value, list) else {}))


def loads(text, fallback=None):
    if not text:
        return fallback if fallback is not None else {}
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return fallback if fallback is not None else {}
