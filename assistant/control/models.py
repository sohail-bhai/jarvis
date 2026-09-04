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


class RiskLevel(str, Enum):
    """How much damage an action could do if it were wrong.

    Risk is a property of the capability, not of the agent asking for it, and
    it is what decides whether the user is interrupted.
    """
    LOW = "low"                  # reading public or harmless information
    MEDIUM = "medium"            # reading private data, sending a message
    HIGH = "high"                # writing, deploying, spending
    CRITICAL = "critical"        # destroying data or changing who has access

    @property
    def rank(self):
        return {"low": 0, "medium": 1, "high": 2, "critical": 3}[self.value]


class Decision(str, Enum):
    """What the policy engine says about one capability request."""
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


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
    CAPABILITY_REQUESTED = "capability_requested"
    CAPABILITY_DENIED = "capability_denied"
    POLICY_CHANGED = "policy_changed"
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
    """A consequential action held until the user decides.

    When an approval carries a capability, approving it is what releases that
    access - the user's decision and the grant are the same event.
    """
    id: str = field(default_factory=new_id)
    task_id: str = ""
    action: str = ""                # short label: "Send email"
    question: str = ""              # what JARVIS is about to do
    reason: str = ""                # why
    impact: str = ""                # what changes
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: float = field(default_factory=now)
    resolved_at: float = 0.0
    capability: str = ""            # what access this releases, if any
    resource: str = ""              # what it applies to
    risk: RiskLevel = RiskLevel.MEDIUM
    agent_id: str = ""              # who asked
    seconds: int = 0                # how long the grant should last

    def to_dict(self):
        return _serialise(self)


@dataclass
class PolicyRule:
    """One allow/deny/ask rule.

    Patterns match capability strings and support a trailing wildcard, so
    `google.gmail.*` covers every Gmail capability. An empty agent, task or
    resource means "any", which is what makes a rule general or specific.
    """
    id: str = field(default_factory=new_id)
    capability: str = "*"
    decision: Decision = Decision.ALLOW
    agent_id: str = ""
    task_id: str = ""
    resource: str = ""
    reason: str = ""
    created_at: float = field(default_factory=now)

    @property
    def specificity(self):
        """How narrowly this rule is aimed. The narrowest rule wins."""
        score = 0
        if self.capability != "*":
            score += 4 if not self.capability.endswith("*") else 2
        if self.agent_id:
            score += 2
        if self.task_id:
            score += 2
        if self.resource:
            score += 1
        return score

    def matches(self, capability, agent_id="", task_id="", resource=""):
        if self.agent_id and self.agent_id != agent_id:
            return False
        if self.task_id and self.task_id != task_id:
            return False
        if self.resource and self.resource != resource:
            return False
        return matches_pattern(self.capability, capability)

    def to_dict(self):
        return _serialise(self)


def matches_pattern(pattern, capability):
    """`*` matches everything, `a.b.*` matches the a.b namespace."""
    if pattern in ("*", capability):
        return True
    if pattern.endswith(".*"):
        return capability.startswith(pattern[:-1])
    return False


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
