"""The control plane itself.

This is the layer that owns coordination: it accepts a goal, records the steps,
picks a helper by capability, grants narrow time-limited access, holds
consequential actions for approval, and writes a readable trail of what
happened. JARVIS owns this state - external frameworks plug into it rather than
replacing it.

Everything here is synchronous and thread-safe so it can be driven equally from
the desktop app, the HTTP API, or a background worker.
"""

import logging
import platform
import socket
import threading

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
    now,
)
from assistant.control.store import ControlStore

logger = logging.getLogger(__name__)

# How long task-scoped access lasts unless the caller says otherwise.
DEFAULT_PERMISSION_SECONDS = 30 * 60


class ControlPlane:
    """Coordinates goals across helpers and devices, and keeps the user in control."""

    def __init__(self, store=None, event_bus=None):
        self.store = store or ControlStore()
        self.event_bus = event_bus
        self._lock = threading.RLock()
        self._subscribers = []
        self._stopped = False

        self.local_device = self._register_local_device()

    # -- subscriptions ------------------------------------------------------

    def subscribe(self, callback):
        """Register a callback for activity events. Returns an unsubscribe fn."""
        with self._lock:
            self._subscribers.append(callback)

        def unsubscribe():
            with self._lock:
                if callback in self._subscribers:
                    self._subscribers.remove(callback)

        return unsubscribe

    def _publish(self, event):
        with self._lock:
            subscribers = list(self._subscribers)

        for callback in subscribers:
            try:
                callback(event)
            except Exception:
                # A broken listener must never derail the work being reported.
                logger.exception("Activity subscriber failed")

    # -- devices ------------------------------------------------------------

    def _register_local_device(self):
        """Make sure the machine JARVIS runs on is always a known device."""
        name = socket.gethostname() or "This computer"
        for device in self.store.list_devices():
            if device.name == name and device.kind == "computer":
                device.status = DeviceStatus.ONLINE
                device.last_seen = now()
                return self.store.save_device(device)

        device = Device(name=name, kind="computer",
                        platform=platform.system().lower(),
                        status=DeviceStatus.ONLINE)
        return self.store.save_device(device)

    def register_device(self, name, kind="computer", platform_name=""):
        device = Device(name=name, kind=kind, platform=platform_name)
        return self.store.save_device(device)

    def list_devices(self):
        return self.store.list_devices()

    # -- helpers ------------------------------------------------------------

    def register_helper(self, name, capabilities, framework="native", device_id=None):
        """Add an AI helper and advertise what it can do."""
        helper = Helper(name=name, framework=framework,
                        device_id=device_id or self.local_device.id,
                        capabilities=list(capabilities))
        self.store.save_helper(helper)
        return helper

    def list_helpers(self):
        return self.store.list_helpers()

    def find_helper_for(self, capability):
        """Pick an available helper that advertises `capability`.

        The user asks for an outcome; this is what turns that into a worker.
        Quarantined and offline helpers are never selected.
        """
        candidates = [
            helper for helper in self.store.list_helpers()
            if helper.can(capability)
            and helper.status in (HelperStatus.IDLE, HelperStatus.WORKING)
        ]
        if not candidates:
            return None
        # Prefer an idle helper, then the least recently used one.
        candidates.sort(key=lambda h: (h.status != HelperStatus.IDLE, h.last_active))
        return candidates[0]

    def quarantine_helper(self, helper_id, reason=""):
        """Isolate a misbehaving helper while keeping it visible."""
        helper = self.store.get_helper(helper_id)
        if helper is None:
            return None
        helper.status = HelperStatus.QUARANTINED
        self.store.save_helper(helper)
        self.record(f"Stopped using {helper.name}." + (f" {reason}" if reason else ""),
                    EventType.NOTE)
        return helper

    # -- tasks --------------------------------------------------------------

    def create_task(self, goal, steps=None, capability=None):
        """Accept a goal and lay out the steps the user will see."""
        if self._stopped:
            raise RuntimeError("JARVIS is stopped. Reset before starting new work.")

        task = Task(goal=goal, status=TaskStatus.PENDING,
                    device_id=self.local_device.id)

        helper = self.find_helper_for(capability) if capability else None
        if helper is not None:
            task.helper_id = helper.id

        self.store.save_task(task)

        for position, label in enumerate(steps or []):
            self.store.save_step(TaskStep(task_id=task.id, position=position, label=label))

        self.record(f"Started working on: {goal}", EventType.TASK_CREATED, task_id=task.id)

        if helper is not None:
            self.record(f"Asked {helper.name} to help.", EventType.HELPER_SELECTED,
                        task_id=task.id)

        return task

    def get_task(self, task_id):
        return self.store.get_task(task_id)

    def list_tasks(self, limit=50, active_only=False):
        return self.store.list_tasks(limit=limit, active_only=active_only)

    def task_detail(self, task_id):
        """A task with its steps and progress, ready for a client to render."""
        task = self.store.get_task(task_id)
        if task is None:
            return None

        steps = self.store.list_steps(task_id)
        done = sum(1 for step in steps if step.status == StepStatus.DONE)

        detail = task.to_dict()
        detail["steps"] = [step.to_dict() for step in steps]
        detail["progress"] = round(done / len(steps), 2) if steps else 0.0
        detail["current_step"] = next(
            (step.label for step in steps if step.status == StepStatus.ACTIVE), "")
        return detail

    def start_step(self, task_id, position):
        """Mark a step as the one being worked on now."""
        steps = self.store.list_steps(task_id)
        target = next((step for step in steps if step.position == position), None)
        if target is None:
            return None

        for step in steps:
            if step.status == StepStatus.ACTIVE:
                step.status = StepStatus.DONE
                self.store.save_step(step)

        target.status = StepStatus.ACTIVE
        self.store.save_step(target)

        task = self.store.get_task(task_id)
        if task and task.status == TaskStatus.PENDING:
            self._set_task_status(task, TaskStatus.RUNNING)

        self.record(target.label, EventType.STEP_STARTED, task_id=task_id)
        return target

    def finish_step(self, task_id, position, detail="", failed=False):
        steps = self.store.list_steps(task_id)
        target = next((step for step in steps if step.position == position), None)
        if target is None:
            return None

        target.status = StepStatus.FAILED if failed else StepStatus.DONE
        target.detail = detail
        self.store.save_step(target)

        self.record(detail or f"Finished: {target.label}",
                    EventType.STEP_FINISHED, task_id=task_id)
        return target

    def complete_task(self, task_id, summary=""):
        task = self.store.get_task(task_id)
        if task is None:
            return None

        for step in self.store.list_steps(task_id):
            if step.status in (StepStatus.PENDING, StepStatus.ACTIVE):
                step.status = StepStatus.DONE
                self.store.save_step(step)

        task.summary = summary
        self._set_task_status(task, TaskStatus.COMPLETED)
        self._release_task_permissions(task_id, "the task finished")
        self.record(summary or "Done.", EventType.TASK_COMPLETED, task_id=task_id)
        return task

    def fail_task(self, task_id, reason=""):
        """Record an honest failure. Never dress this up as success."""
        task = self.store.get_task(task_id)
        if task is None:
            return None

        task.summary = reason
        self._set_task_status(task, TaskStatus.FAILED)
        self._release_task_permissions(task_id, "the task stopped")
        self.record(reason or "Couldn't finish this step.",
                    EventType.TASK_FAILED, task_id=task_id)
        return task

    def cancel_task(self, task_id, reason="You stopped this."):
        task = self.store.get_task(task_id)
        if task is None or task.status.is_terminal:
            return task

        self._set_task_status(task, TaskStatus.CANCELLED)
        self._release_task_permissions(task_id, "the task was stopped")
        self.record(reason, EventType.TASK_CANCELLED, task_id=task_id)
        return task

    def save_checkpoint(self, task_id, checkpoint):
        """Persist enough state to resume this task after an interruption."""
        task = self.store.get_task(task_id)
        if task is None:
            return None
        task.checkpoint = checkpoint
        task.updated_at = now()
        return self.store.save_task(task)

    def _set_task_status(self, task, status):
        task.status = status
        task.updated_at = now()
        self.store.save_task(task)

    # -- permissions --------------------------------------------------------

    def grant(self, resource, actions, task_id="", seconds=DEFAULT_PERMISSION_SECONDS,
              device_id=""):
        """Grant narrow, time-limited access for one task."""
        permission = Permission(
            task_id=task_id, resource=resource, actions=list(actions),
            device_id=device_id or self.local_device.id,
            expires_at=now() + seconds,
        )
        self.store.save_permission(permission)

        minutes = max(1, int(seconds // 60))
        self.record(
            f"Allowed {' and '.join(actions)} access to {resource} for {minutes} minutes.",
            EventType.PERMISSION_GRANTED, task_id=task_id)
        return permission

    def check(self, resource, action, task_id=""):
        """Is this action allowed on this resource right now?"""
        moment = now()
        for permission in self.store.list_permissions(active_only=True):
            if permission.resource != resource:
                continue
            if task_id and permission.task_id and permission.task_id != task_id:
                continue
            if permission.allows(action, moment):
                return True
        return False

    def revoke(self, permission_id, reason=""):
        permission = self.store.get_permission(permission_id)
        if permission is None:
            return None

        permission.status = PermissionStatus.REVOKED
        self.store.save_permission(permission)
        self.record(f"Removed access to {permission.resource}."
                    + (f" {reason}" if reason else ""),
                    EventType.PERMISSION_REVOKED, task_id=permission.task_id)
        return permission

    def expire_permissions(self):
        """Mark lapsed grants expired. Safe to call repeatedly."""
        moment = now()
        expired = []
        for permission in self.store.list_permissions(active_only=True):
            if moment >= permission.expires_at:
                permission.status = PermissionStatus.EXPIRED
                self.store.save_permission(permission)
                expired.append(permission)
        return expired

    def list_permissions(self, active_only=True):
        self.expire_permissions()
        return self.store.list_permissions(active_only=active_only)

    def _release_task_permissions(self, task_id, reason):
        for permission in self.store.list_permissions(active_only=True, task_id=task_id):
            permission.status = PermissionStatus.REVOKED
            self.store.save_permission(permission)

    # -- approvals ----------------------------------------------------------

    def request_approval(self, action, question, reason="", impact="", task_id=""):
        """Hold a consequential action until the user decides."""
        approval = Approval(task_id=task_id, action=action, question=question,
                            reason=reason, impact=impact)
        self.store.save_approval(approval)

        if task_id:
            task = self.store.get_task(task_id)
            if task is not None and not task.status.is_terminal:
                self._set_task_status(task, TaskStatus.WAITING_APPROVAL)

        self.record(f"Waiting for your approval: {question}",
                    EventType.APPROVAL_REQUESTED, task_id=task_id,
                    metadata={"approval_id": approval.id})
        return approval

    def resolve_approval(self, approval_id, approved):
        approval = self.store.get_approval(approval_id)
        if approval is None or approval.status != ApprovalStatus.PENDING:
            return None

        approval.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.DECLINED
        approval.resolved_at = now()
        self.store.save_approval(approval)

        if approval.task_id:
            task = self.store.get_task(approval.task_id)
            if task is not None and task.status == TaskStatus.WAITING_APPROVAL:
                self._set_task_status(
                    task, TaskStatus.RUNNING if approved else TaskStatus.CANCELLED)

        self.record(
            f"You approved: {approval.action}" if approved
            else f"You declined: {approval.action}",
            EventType.APPROVAL_RESOLVED, task_id=approval.task_id,
            metadata={"approval_id": approval.id, "approved": approved})
        return approval

    def list_approvals(self, pending_only=True):
        return self.store.list_approvals(pending_only=pending_only)

    # -- activity -----------------------------------------------------------

    def record(self, message, event_type=EventType.NOTE, task_id="",
               actor="JARVIS", metadata=None):
        """Write one plain-English line to the timeline and notify listeners."""
        event = ActivityEvent(task_id=task_id, type=event_type, message=message,
                              actor=actor, device_id=self.local_device.id,
                              metadata=metadata or {})
        self.store.save_event(event)
        self._publish(event)
        return event

    def list_events(self, limit=100, task_id=None):
        return self.store.list_events(limit=limit, task_id=task_id)

    # -- emergency stop -----------------------------------------------------

    def emergency_stop(self):
        """Stop active work, revoke access, and refuse new tasks.

        This never deletes user data. It cancels what is running, invalidates
        every temporary grant, and latches until `resume()` is called.
        """
        cancelled, revoked = 0, 0

        for task in self.store.list_tasks(limit=500, active_only=True):
            self._set_task_status(task, TaskStatus.CANCELLED)
            cancelled += 1

        for permission in self.store.list_permissions(active_only=True):
            permission.status = PermissionStatus.REVOKED
            self.store.save_permission(permission)
            revoked += 1

        for approval in self.store.list_approvals(pending_only=True):
            approval.status = ApprovalStatus.DECLINED
            approval.resolved_at = now()
            self.store.save_approval(approval)

        for helper in self.store.list_helpers():
            if helper.status == HelperStatus.WORKING:
                helper.status = HelperStatus.IDLE
                helper.current_task_id = ""
                self.store.save_helper(helper)

        self._stopped = True
        self.record(
            f"Emergency stop. Stopped {cancelled} task"
            f"{'s' if cancelled != 1 else ''} and removed {revoked} temporary "
            f"permission{'s' if revoked != 1 else ''}.",
            EventType.EMERGENCY_STOP)

        return {"stopped": True, "tasks_cancelled": cancelled,
                "permissions_revoked": revoked}

    def resume(self):
        """Allow new work again after an emergency stop."""
        self._stopped = False
        self.record("JARVIS is accepting new work again.", EventType.NOTE)
        return {"stopped": False}

    @property
    def is_stopped(self):
        return self._stopped

    # -- summary ------------------------------------------------------------

    def status(self):
        """A small snapshot for a home screen or security page."""
        self.expire_permissions()
        return {
            "stopped": self._stopped,
            "devices": len(self.store.list_devices()),
            "helpers": len(self.store.list_helpers()),
            "active_tasks": len(self.store.list_tasks(limit=500, active_only=True)),
            "pending_approvals": len(self.store.list_approvals(pending_only=True)),
            "temporary_access": len(self.store.list_permissions(active_only=True)),
        }


_control_plane = None
_singleton_lock = threading.Lock()


def get_control_plane(event_bus=None):
    """Shared instance used by the desktop app and the API."""
    global _control_plane
    with _singleton_lock:
        if _control_plane is None:
            _control_plane = ControlPlane(event_bus=event_bus)
        return _control_plane


def reset_control_plane():
    """Drop the shared instance. Used by tests."""
    global _control_plane
    with _singleton_lock:
        if _control_plane is not None:
            _control_plane.store.close()
        _control_plane = None
