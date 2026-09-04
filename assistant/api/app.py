"""HTTP and WebSocket boundary for the JARVIS control plane.

This is the seam between the JARVIS core and any client: the desktop app on
Windows, macOS or Linux, and the mobile interface. Clients hold no logic of
their own - they read state here and post user decisions back, so every client
sees the same tasks, approvals and activity.

Run it with:

    python -m assistant.api                 # localhost only
    python -m assistant.api --host 0.0.0.0  # reachable from a phone

Binding to 0.0.0.0 exposes control of this computer to the local network, so it
is opt-in and warns on startup. Remote clients must pair first and then carry a
device token; see `assistant/api/auth.py`.
"""

import argparse
import asyncio
import logging

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from assistant.api.auth import (
    ApiSecurity,
    PairingError,
    RateLimited,
    bearer_token,
)
from assistant.api.errors import error_body, install_error_handlers
from assistant.control.capabilities import catalog
from assistant.control.executor import get_executor
from assistant.control.service import get_control_plane

logger = logging.getLogger(__name__)

API_VERSION = "1"


# -- request bodies ---------------------------------------------------------

class PlannedStep(BaseModel):
    label: str = Field(..., min_length=1, description="What JARVIS will do.")
    depends_on: list[int] = Field(default_factory=list,
                                  description="Positions that must finish first.")
    agent_id: str = Field("", description="Which agent should do it.")
    capability: str = Field("", description="Access this step needs.")


class CreateTaskRequest(BaseModel):
    goal: str = Field(..., min_length=1, description="What the user asked for.")
    steps: list[str] = Field(default_factory=list,
                             description="Observable steps, run in order.")
    plan: list[PlannedStep] = Field(
        default_factory=list,
        description="Steps as a graph. Steps with no dependencies run together.")
    capability: str = Field("", description="Capability needed, e.g. 'research'.")
    run: bool = Field(False,
                      description="Start working the steps immediately.")
    autoplan: bool = Field(False,
                           description="Let JARVIS break the goal into steps.")


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
    framework: str = Field("native", description="native, http, mcp, langgraph, crewai.")
    version: str = ""
    endpoint: str = Field("", description="Where a remote agent is reached.")
    metadata: dict = Field(default_factory=dict)


class HeartbeatRequest(BaseModel):
    status: str = Field("", description="idle, working or offline.")
    latency_ms: int | None = Field(None, ge=0, description="How long the last work took.")
    ok: bool | None = Field(None, description="Whether the last work succeeded.")


class KillAgentRequest(BaseModel):
    reason: str = ""


class RegisterDeviceRequest(BaseModel):
    name: str
    kind: str = "computer"
    platform: str = ""
    capabilities: list[str] = Field(default_factory=list)


class DeviceHeartbeatRequest(BaseModel):
    capabilities: list[str] | None = None


class StepUpdateRequest(BaseModel):
    position: int
    detail: str = ""
    failed: bool = False


class CapabilityRequest(BaseModel):
    capability: str = Field(..., min_length=1,
                            description="Namespaced capability, e.g. 'google.gmail.read'.")
    agent_id: str = Field("", description="Which agent is asking.")
    task_id: str = Field("", description="The task this belongs to.")
    resource: str = Field("", description="What it applies to, if narrower than the capability.")
    seconds: int = Field(1800, gt=0, le=24 * 3600)
    reason: str = Field("", description="Why this is needed, shown to the user.")


class PolicyRuleRequest(BaseModel):
    capability: str = Field(..., min_length=1,
                            description="Capability or pattern, e.g. 'google.*'.")
    decision: str = Field(..., description="allow, require_approval or deny.")
    agent_id: str = ""
    task_id: str = ""
    resource: str = ""
    reason: str = ""


class DelegateRequest(BaseModel):
    label: str = Field(..., min_length=1, description="What the other agent should do.")
    capability: str = Field("", description="Capability the work needs.")
    agent_id: str = Field("", description="A specific agent, if it matters.")
    after: list[int] | None = Field(
        None, description="Positions this must wait for. Defaults to the unfinished ones.")


class PairRequest(BaseModel):
    code: str = Field(..., min_length=4, description="The pairing code shown on the computer.")
    name: str = Field("", description="What to call this device, e.g. 'Rav's phone'.")
    kind: str = Field("phone", description="phone, computer, server, tablet.")
    platform: str = Field("", description="android, ios, windows, darwin, linux.")


# Paths that must work before a client holds a token.
OPEN_PATHS = ("/", "/health", "/docs", "/redoc", "/openapi.json",
              "/api/pair", "/api/pair/code")


def create_app(control=None, executor=None, security=None):
    """Build the API.

    Accepts a control plane, an executor and a security policy so tests, and
    any embedding app, can inject their own instead of driving the shared ones.
    """
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
    runner = executor or get_executor(plane=plane)
    guard = security if security is not None else ApiSecurity(plane.store)
    app.state.control = plane
    app.state.executor = runner
    app.state.security = guard

    install_error_handlers(app)

    @app.middleware("http")
    async def authenticate_and_limit(request: Request, call_next):
        """Every call names a device, and no device may flood the API."""
        path = request.url.path
        client_host = request.client.host if request.client else ""

        if path in OPEN_PATHS or path.startswith("/docs") or path.startswith("/static"):
            # Open to everyone, but a token still names the caller: pairing a
            # second device from a phone depends on knowing who is asking.
            device = guard.device_for_token(
                bearer_token(request.headers.get("authorization")))
        else:
            try:
                device = guard.authenticate(
                    bearer_token(request.headers.get("authorization")), client_host)
            except PermissionError as error:
                return JSONResponse(status_code=401,
                                    content=error_body(401, str(error)))

        try:
            guard.check_rate(device.id if device is not None else client_host or "local")
        except RateLimited as error:
            return JSONResponse(
                status_code=429,
                content=error_body(429, "Too many requests. Slow down."),
                headers={"Retry-After": str(error.retry_after)})

        request.state.device = device
        return await call_next(request)

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

    # -- pairing -----------------------------------------------------------

    @app.post("/api/pair/code", tags=["security"])
    def pairing_code(request: Request):
        """Mint a short-lived code for a new device to claim.

        Only this computer, or an already paired device, may do this - it is
        the step that decides who gets to control the machine.
        """
        if not guard.may_pair(getattr(request.state, "device", None),
                              request.client.host if request.client else ""):
            raise HTTPException(status_code=403,
                                detail="Ask for a pairing code on the computer itself.")
        return guard.issue_pairing_code()

    @app.post("/api/pair", status_code=201, tags=["security"])
    def pair_device(request: PairRequest):
        """Trade a pairing code for a device token. The token is shown once."""
        try:
            device, token = guard.pair(request.code, request.name,
                                       kind=request.kind, platform=request.platform)
        except PairingError as error:
            raise HTTPException(status_code=403, detail=str(error))

        plane.record(f"Paired a new device: {device.name}.")
        return {"device": device.to_dict(), "token": token,
                "note": "Store this token now. It is not shown again."}

    @app.delete("/api/devices/{device_id}/token", tags=["security"])
    def unpair_device(device_id: str):
        """Revoke one device's access without touching any other device."""
        device = guard.unpair(device_id)
        if device is None:
            raise HTTPException(status_code=404, detail="No such device.")
        plane.record(f"Revoked access for {device.name}.")
        return device.to_dict()

    # -- tasks -------------------------------------------------------------

    @app.get("/api/tasks", tags=["tasks"])
    def list_tasks(limit: int = 50, active_only: bool = False):
        return [task.to_dict()
                for task in plane.list_tasks(limit=limit, active_only=active_only)]

    @app.post("/api/tasks", status_code=201, tags=["tasks"])
    def create_task(request: CreateTaskRequest):
        steps = [step.model_dump() for step in request.plan] or request.steps
        if not steps and request.autoplan:
            steps = runner.planner.plan(request.goal)

        try:
            task = plane.create_task(request.goal, steps=steps,
                                     capability=request.capability or None)
        except RuntimeError as error:
            # Raised while an emergency stop is latched.
            raise HTTPException(status_code=409, detail=str(error))

        if request.run:
            runner.submit(task.id)

        return plane.task_detail(task.id)

    @app.get("/api/tasks/{task_id}", tags=["tasks"])
    def get_task(task_id: str):
        detail = plane.task_detail(task_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="No such task.")
        return detail

    @app.post("/api/tasks/{task_id}/run", status_code=202, tags=["tasks"])
    def run_task(task_id: str):
        """Hand the task's steps to the AI brain and work them in order.

        This returns as soon as the work starts. Progress arrives over
        /ws/activity, or by polling the task.
        """
        if plane.is_stopped:
            raise HTTPException(status_code=409,
                                detail="JARVIS is stopped. Resume before starting work.")

        task = plane.get_task(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="No such task.")
        if task.status.is_terminal:
            raise HTTPException(status_code=409, detail="This task already finished.")

        runner.submit(task_id)
        return plane.task_detail(task_id)

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
        """Stop a task. A step already running is interrupted, not waited on."""
        if plane.get_task(task_id) is None:
            raise HTTPException(status_code=404, detail="No such task.")
        runner.stop(task_id)
        return plane.task_detail(task_id)

    @app.post("/api/tasks/{task_id}/delegate", status_code=201, tags=["tasks"])
    def delegate_step(task_id: str, request: DelegateRequest):
        """Hand part of this task to another agent, under the same task."""
        if plane.get_task(task_id) is None:
            raise HTTPException(status_code=404, detail="No such task.")

        step = plane.delegate(task_id, request.label, capability=request.capability,
                              agent_id=request.agent_id, after=request.after)
        if step is None:
            raise HTTPException(
                status_code=409,
                detail="No agent is available with that capability.")
        return step.to_dict()

    @app.post("/api/tasks/resume", tags=["tasks"])
    def resume_interrupted():
        """Pick up tasks that were running when JARVIS last stopped."""
        return [task.to_dict() for task in runner.resume_interrupted()]

    @app.post("/api/tasks/plan", tags=["tasks"])
    def plan_goal(request: CreateTaskRequest):
        """Break a goal into steps without committing to running them."""
        return {"goal": request.goal, "steps": runner.planner.plan(request.goal)}

    # -- capabilities and policy -------------------------------------------

    @app.get("/api/capabilities", tags=["security"])
    def list_capabilities(prefix: str = ""):
        """Everything an agent may ask for, with the risk each one carries."""
        return catalog(prefix)

    @app.post("/api/capabilities/request", tags=["security"])
    def request_capability(request: CapabilityRequest):
        """Ask for access. Answers granted, waiting on you, or denied."""
        try:
            return plane.request_capability(
                request.capability, agent_id=request.agent_id,
                task_id=request.task_id, resource=request.resource,
                seconds=request.seconds, reason=request.reason)
        except RuntimeError as error:
            raise HTTPException(status_code=409, detail=str(error))

    @app.get("/api/policies", tags=["security"])
    def list_policies():
        return [rule.to_dict() for rule in plane.list_policy_rules()]

    @app.post("/api/policies", status_code=201, tags=["security"])
    def add_policy(request: PolicyRuleRequest):
        try:
            rule = plane.add_policy_rule(
                request.capability, request.decision, agent_id=request.agent_id,
                task_id=request.task_id, resource=request.resource,
                reason=request.reason)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="Decision must be allow, require_approval or deny.")
        return rule.to_dict()

    @app.delete("/api/policies/{rule_id}", tags=["security"])
    def remove_policy(rule_id: str):
        rule = plane.remove_policy_rule(rule_id)
        if rule is None:
            raise HTTPException(status_code=404, detail="No such policy rule.")
        return rule.to_dict()

    # -- devices and helpers ----------------------------------------------

    @app.get("/api/devices", tags=["devices"])
    def list_devices():
        return [device.to_dict() for device in plane.list_devices()]

    @app.post("/api/devices", status_code=201, tags=["devices"])
    def register_device(request: RegisterDeviceRequest):
        device = plane.register_device(request.name, kind=request.kind,
                                       platform_name=request.platform,
                                       capabilities=request.capabilities)
        return device.to_dict()

    @app.post("/api/devices/{device_id}/heartbeat", tags=["devices"])
    def device_heartbeat(device_id: str, request: DeviceHeartbeatRequest):
        """A device says it is still here, and what it can do."""
        device = plane.device_heartbeat(device_id, capabilities=request.capabilities)
        if device is None:
            raise HTTPException(status_code=404, detail="No such device.")
        return device.to_dict()

    # -- agents -------------------------------------------------------------
    # /api/helpers is the older name for the same thing and still works.

    @app.get("/api/agents", tags=["agents"])
    @app.get("/api/helpers", tags=["helpers"])
    def list_agents():
        return [helper.to_dict() for helper in plane.list_helpers()]

    @app.post("/api/agents", status_code=201, tags=["agents"])
    @app.post("/api/helpers", status_code=201, tags=["helpers"])
    def register_agent(request: RegisterHelperRequest):
        helper = plane.register_helper(request.name, request.capabilities,
                                       framework=request.framework,
                                       version=request.version,
                                       endpoint=request.endpoint,
                                       metadata=request.metadata)
        return helper.to_dict()

    @app.get("/api/agents/health", tags=["agents"])
    def agent_health():
        """One row per agent: status, error rate and slow-end latency."""
        return plane.agent_health()

    @app.get("/api/agents/{agent_id}", tags=["agents"])
    def get_agent(agent_id: str):
        helper = plane.get_helper(agent_id)
        if helper is None:
            raise HTTPException(status_code=404, detail="No such agent.")
        return helper.to_dict()

    @app.post("/api/agents/{agent_id}/heartbeat", tags=["agents"])
    def agent_heartbeat(agent_id: str, request: HeartbeatRequest):
        """An agent reports that it is alive, and how its last work went."""
        try:
            helper = plane.heartbeat(agent_id, latency_ms=request.latency_ms,
                                     ok=request.ok, status=request.status or None)
        except ValueError:
            raise HTTPException(status_code=422,
                                detail="Status must be idle, working or offline.")
        if helper is None:
            raise HTTPException(status_code=404, detail="No such agent.")
        return helper.to_dict()

    @app.post("/api/agents/{agent_id}/enable", tags=["agents"])
    def enable_agent(agent_id: str):
        helper = plane.set_helper_enabled(agent_id, True)
        if helper is None:
            raise HTTPException(status_code=404, detail="No such agent.")
        return helper.to_dict()

    @app.post("/api/agents/{agent_id}/disable", tags=["agents"])
    def disable_agent(agent_id: str):
        """Stop giving this agent work, without forgetting what it did."""
        helper = plane.set_helper_enabled(agent_id, False)
        if helper is None:
            raise HTTPException(status_code=404, detail="No such agent.")
        return helper.to_dict()

    @app.post("/api/agents/{agent_id}/kill", tags=["security"])
    def kill_agent(agent_id: str, request: KillAgentRequest):
        """Stop an agent now: its work, its access, and any future request."""
        helper = plane.kill_helper(agent_id, reason=request.reason)
        if helper is None:
            raise HTTPException(status_code=404, detail="No such agent.")
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
    async def activity_stream(websocket: WebSocket, token: str = ""):
        """Pushes activity events to a client as they happen.

        A socket carries the same authority as the REST API, so it is
        authenticated the same way - by token, or by being local.
        """
        try:
            guard.authenticate(
                token or bearer_token(websocket.headers.get("authorization")),
                websocket.client.host if websocket.client else "")
        except PermissionError:
            await websocket.close(code=1008)
            return

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
