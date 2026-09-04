"""HTTP and WebSocket boundary for the JARVIS control plane.

This is the seam between the JARVIS core and any client: the desktop app on
Windows, macOS or Linux, and the mobile interface. Clients hold no logic of
their own - they read state here and post user decisions back, so every client
sees the same tasks, approvals and activity.

Run it with:

    python -m assistant.api                 # localhost only
    python -m assistant.api --host 0.0.0.0  # reachable from a phone

Binding to 0.0.0.0 exposes control of this computer to the local network, so it
is opt-in and warns on startup.
"""

import argparse
import asyncio
import logging

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from assistant.control.service import get_control_plane

logger = logging.getLogger(__name__)

API_VERSION = "1"


# -- request bodies ---------------------------------------------------------

class CreateTaskRequest(BaseModel):
    goal: str = Field(..., min_length=1, description="What the user asked for.")
    steps: list[str] = Field(default_factory=list,
                             description="Observable steps, in plain language.")
    capability: str = Field("", description="Capability needed, e.g. 'research'.")


class ResolveApprovalRequest(BaseModel):
    approved: bool


class GrantRequest(BaseModel):
    resource: str
    actions: list[str]
    task_id: str = ""
    seconds: int = Field(1800, gt=0, le=24 * 3600)


class RegisterHelperRequest(BaseModel):
    name: str
    capabilities: list[str]
    framework: str = "native"


class StepUpdateRequest(BaseModel):
    position: int
    detail: str = ""
    failed: bool = False


def create_app(control=None):
    """Build the API. Accepts a control plane so tests can inject their own."""
    app = FastAPI(
        title="JARVIS Control Plane",
        version=API_VERSION,
        description="Goals, helpers, devices, permissions and activity.",
    )

    # The desktop and mobile clients are separate origins.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    plane = control or get_control_plane()
    app.state.control = plane

    # -- health and status -------------------------------------------------

    @app.get("/", tags=["system"])
    def root():
        """Point a browser at something useful instead of a bare 404."""
        return {
            "name": "JARVIS Control Plane",
            "version": API_VERSION,
            "documentation": "/docs",
            "endpoints": {
                "status": "/api/status",
                "tasks": "/api/tasks",
                "devices": "/api/devices",
                "helpers": "/api/helpers",
                "approvals": "/api/approvals",
                "permissions": "/api/permissions",
                "activity": "/api/activity",
                "live_activity": "/ws/activity",
            },
        }

    @app.get("/health", tags=["system"])
    def health():
        return {"ok": True, "version": API_VERSION}

    @app.get("/api/status", tags=["system"])
    def status():
        return plane.status()

    # -- tasks -------------------------------------------------------------

    @app.get("/api/tasks", tags=["tasks"])
    def list_tasks(limit: int = 50, active_only: bool = False):
        return [task.to_dict()
                for task in plane.list_tasks(limit=limit, active_only=active_only)]

    @app.post("/api/tasks", status_code=201, tags=["tasks"])
    def create_task(request: CreateTaskRequest):
        try:
            task = plane.create_task(request.goal, steps=request.steps,
                                     capability=request.capability or None)
        except RuntimeError as error:
            # Raised while an emergency stop is latched.
            raise HTTPException(status_code=409, detail=str(error))
        return plane.task_detail(task.id)

    @app.get("/api/tasks/{task_id}", tags=["tasks"])
    def get_task(task_id: str):
        detail = plane.task_detail(task_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="No such task.")
        return detail

    @app.post("/api/tasks/{task_id}/steps/start", tags=["tasks"])
    def start_step(task_id: str, request: StepUpdateRequest):
        step = plane.start_step(task_id, request.position)
        if step is None:
            raise HTTPException(status_code=404, detail="No such step.")
        return step.to_dict()

    @app.post("/api/tasks/{task_id}/steps/finish", tags=["tasks"])
    def finish_step(task_id: str, request: StepUpdateRequest):
        step = plane.finish_step(task_id, request.position,
                                 detail=request.detail, failed=request.failed)
        if step is None:
            raise HTTPException(status_code=404, detail="No such step.")
        return step.to_dict()

    @app.post("/api/tasks/{task_id}/complete", tags=["tasks"])
    def complete_task(task_id: str, summary: str = ""):
        task = plane.complete_task(task_id, summary=summary)
        if task is None:
            raise HTTPException(status_code=404, detail="No such task.")
        return plane.task_detail(task_id)

    @app.post("/api/tasks/{task_id}/cancel", tags=["tasks"])
    def cancel_task(task_id: str):
        task = plane.cancel_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="No such task.")
        return plane.task_detail(task_id)

    # -- devices and helpers ----------------------------------------------

    @app.get("/api/devices", tags=["devices"])
    def list_devices():
        return [device.to_dict() for device in plane.list_devices()]

    @app.get("/api/helpers", tags=["helpers"])
    def list_helpers():
        return [helper.to_dict() for helper in plane.list_helpers()]

    @app.post("/api/helpers", status_code=201, tags=["helpers"])
    def register_helper(request: RegisterHelperRequest):
        helper = plane.register_helper(request.name, request.capabilities,
                                       framework=request.framework)
        return helper.to_dict()

    # -- approvals ---------------------------------------------------------

    @app.get("/api/approvals", tags=["approvals"])
    def list_approvals(pending_only: bool = True):
        return [approval.to_dict()
                for approval in plane.list_approvals(pending_only=pending_only)]

    @app.post("/api/approvals/{approval_id}", tags=["approvals"])
    def resolve_approval(approval_id: str, request: ResolveApprovalRequest):
        approval = plane.resolve_approval(approval_id, request.approved)
        if approval is None:
            raise HTTPException(status_code=404,
                                detail="No such approval, or it was already decided.")
        return approval.to_dict()

    # -- permissions -------------------------------------------------------

    @app.get("/api/permissions", tags=["security"])
    def list_permissions(active_only: bool = True):
        return [permission.to_dict()
                for permission in plane.list_permissions(active_only=active_only)]

    @app.post("/api/permissions", status_code=201, tags=["security"])
    def grant_permission(request: GrantRequest):
        permission = plane.grant(request.resource, request.actions,
                                 task_id=request.task_id, seconds=request.seconds)
        return permission.to_dict()

    @app.delete("/api/permissions/{permission_id}", tags=["security"])
    def revoke_permission(permission_id: str):
        permission = plane.revoke(permission_id)
        if permission is None:
            raise HTTPException(status_code=404, detail="No such permission.")
        return permission.to_dict()

    # -- activity ----------------------------------------------------------

    @app.get("/api/activity", tags=["activity"])
    def list_activity(limit: int = 100, task_id: str = ""):
        return [event.to_dict()
                for event in plane.list_events(limit=limit, task_id=task_id or None)]

    # -- emergency stop ----------------------------------------------------

    @app.post("/api/emergency-stop", tags=["security"])
    def emergency_stop():
        return plane.emergency_stop()

    @app.post("/api/resume", tags=["security"])
    def resume():
        return plane.resume()

    # -- live activity stream ----------------------------------------------

    @app.websocket("/ws/activity")
    async def activity_stream(websocket: WebSocket):
        """Pushes activity events to a client as they happen."""
        await websocket.accept()

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue(maxsize=200)

        def on_event(event):
            # Called from worker threads, so hop back onto the event loop.
            loop.call_soon_threadsafe(_offer, event)

        def _offer(event):
            try:
                queue.put_nowait(event.to_dict())
            except asyncio.QueueFull:
                pass  # A slow client must not stall the control plane.

        unsubscribe = plane.subscribe(on_event)

        try:
            # Send recent history first so a client opens with context.
            for event in reversed(plane.list_events(limit=25)):
                await websocket.send_json(event.to_dict())

            while True:
                await websocket.send_json(await queue.get())
        except WebSocketDisconnect:
            pass
        except Exception:
            logger.exception("Activity stream failed")
        finally:
            unsubscribe()

    return app


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run the JARVIS control plane API.")
    parser.add_argument("--host", default="127.0.0.1",
                        help="Bind address. Use 0.0.0.0 to allow phone access.")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    import uvicorn

    from assistant import logging_setup
    logging_setup.configure_logging()

    if args.host not in ("127.0.0.1", "localhost"):
        logger.warning(
            "Listening on %s. Anything on your network can control this computer. "
            "Only do this on a network you trust.", args.host)

    uvicorn.run(create_app(), host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
