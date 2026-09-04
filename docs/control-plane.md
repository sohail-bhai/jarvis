# JARVIS Control Plane

The control plane is the part of JARVIS that coordinates work. It accepts a
goal in plain language, breaks it into observable steps, picks an AI helper by
what that helper can do, grants narrow and time-limited access, holds
consequential actions until the user approves them, and records a readable
trail of everything that happened.

It is deliberately separate from voice, the desktop UI and the AI brain, so
every client sees the same state.

```
Desktop app (Windows / macOS / Linux)     Mobile client
                    \                        /
                     \                      /
                      HTTP + WebSocket API
                              |
                        Control plane
                              |
                       SQLite (data/control.db)
```

## Why a service boundary

The desktop app and the mobile interface are built by different people. If
coordination logic lived inside the desktop UI, the phone could not reach it.
Putting it behind an API means:

- the desktop app is a thin client and can be rewritten freely,
- the mobile client gets the same capabilities with no duplicated logic,
- tasks, approvals and activity stay consistent across both.

## Modules

| File | Responsibility |
| --- | --- |
| `assistant/control/models.py` | The data model: `Task`, `TaskStep`, `Helper`, `Device`, `Permission`, `Approval`, `ActivityEvent`, plus their status enums. Plain dataclasses with no framework dependency. |
| `assistant/control/store.py` | SQLite persistence. The only module that knows SQL, so moving to PostgreSQL later means rewriting this file alone. |
| `assistant/control/service.py` | `ControlPlane` — the coordination logic and the only thing clients need. |
| `assistant/api.py` | FastAPI HTTP + WebSocket boundary. |

## Core concepts

**Task** — a goal in the user's own words, with ordered **steps** phrased so a
person can read them ("Finding relevant files"). Progress is derived from how
many steps are done, so no client has to compute it.

**Helper** — an AI helper that advertises capabilities. Callers ask for a
capability, never for a helper by name:

```python
plane.create_task("Look this up", capability="research")
```

A helper that is offline or quarantined is never selected.

**Permission** — access scoped to a resource, a set of actions, a task and an
expiry. Grants are released automatically when their task finishes.

**Approval** — a consequential action held until the user decides. Requesting
one moves the task to `waiting_approval`; approving resumes it, declining
cancels it.

**ActivityEvent** — one line of the timeline, in plain English. This is what
the System Log renders. It records observable actions only, never model
reasoning.

## Using it from Python

```python
from assistant.control import get_control_plane

plane = get_control_plane()

plane.register_helper("Research helper", ["research", "web"])

task = plane.create_task(
    "Continue my Hackwave project",
    steps=["Finding relevant files", "Researching on the web", "Preparing the document"],
    capability="research",
)

plane.start_step(task.id, 0)
plane.finish_step(task.id, 0, "Found 3 matching documents")

plane.grant("Hackwave project", ["read", "write"], task_id=task.id, seconds=1800)

approval = plane.request_approval(
    action="Merge changes",
    question="I'm ready to merge your project changes.",
    reason="You asked me to finish the project",
    impact="14 files will change. All tests passed.",
    task_id=task.id,
)
plane.resolve_approval(approval.id, approved=True)

plane.complete_task(task.id, "Your project has been updated.")
```

## Running the API

```bash
python -m assistant.api                 # localhost only (default)
python -m assistant.api --host 0.0.0.0  # reachable from a phone
python -m assistant.api --port 8765
```

Interactive documentation is generated at `http://127.0.0.1:8765/docs`.

> Binding to `0.0.0.0` lets anything on your network control this computer.
> It is opt-in and logs a warning on startup. Only use it on a network you
> trust. There is no authentication yet — see Limitations.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness check. |
| `GET` | `/api/status` | Counts for a home or security screen. |
| `GET` | `/api/tasks` | List tasks. `?active_only=true` hides finished ones. |
| `POST` | `/api/tasks` | Create a task from a goal and its steps. |
| `GET` | `/api/tasks/{id}` | One task with steps, progress and current step. |
| `POST` | `/api/tasks/{id}/steps/start` | Mark a step as being worked on. |
| `POST` | `/api/tasks/{id}/steps/finish` | Finish a step, optionally as failed. |
| `POST` | `/api/tasks/{id}/complete` | Complete a task with a summary. |
| `POST` | `/api/tasks/{id}/cancel` | Stop a task. |
| `GET` | `/api/devices` | Known machines. |
| `GET`/`POST` | `/api/helpers` | List or register AI helpers. |
| `GET` | `/api/approvals` | Pending approvals by default. |
| `POST` | `/api/approvals/{id}` | Approve or decline. |
| `GET`/`POST` | `/api/permissions` | List or grant temporary access. |
| `DELETE` | `/api/permissions/{id}` | Revoke a grant. |
| `GET` | `/api/activity` | Timeline, newest first. |
| `POST` | `/api/emergency-stop` | Stop work and revoke all access. |
| `POST` | `/api/resume` | Accept work again. |
| `WS` | `/ws/activity` | Live activity stream. |

### Live activity

`/ws/activity` sends the 25 most recent events on connect so a client opens
with context, then pushes new events as they happen.

```javascript
const socket = new WebSocket("ws://127.0.0.1:8765/ws/activity");
socket.onmessage = (event) => {
  const activity = JSON.parse(event.data);
  console.log(activity.timestamp, activity.message);
};
```

A slow client is never allowed to stall the control plane: its queue is
bounded and events are dropped rather than buffered without limit.

## Emergency stop

`POST /api/emergency-stop` cancels active tasks, revokes every temporary
permission, declines pending approvals and releases busy helpers. It then
latches: new tasks are refused with `409` until `POST /api/resume`.

It never deletes user data. History stays intact so the user can see what was
stopped.

## Design decisions

- **SQLite, not PostgreSQL.** No server to run. Storage is isolated in
  `store.py`, so swapping it later touches one file.
- **Dataclasses, not ORM models.** The model crosses SQLite, JSON and the
  event bus without dragging a framework along.
- **Synchronous core, async only at the edge.** The control plane is
  thread-safe and callable from anywhere; only the WebSocket handler is async.
- **Failures are recorded honestly.** `fail_task` stores the real reason. The
  timeline never claims something worked when it did not.

## Limitations

These are known gaps, not oversights:

- **No authentication.** Anyone who can reach the port can drive the control
  plane. This is why it binds to localhost by default. An API key or paired
  device token is needed before real remote use.
- **Helper selection is a first match, not a scheduler.** It prefers idle then
  least-recently-used. There is no load balancing or cost awareness.
- **Steps are recorded, not executed.** The control plane tracks and
  coordinates work; connecting steps to the existing tool loop in
  `assistant/ai_brain.py` is separate work.
- **Checkpoints are stored but not yet replayed.** `save_checkpoint` persists
  state; automatic recovery onto another helper is not implemented.
- **Permission expiry is checked on read**, not by a background timer. A grant
  stops authorising the moment it lapses, but its stored status only flips to
  `expired` the next time permissions are listed or checked.

## Tests

```bash
python -m unittest tests.test_control_plane tests.test_api
```

52 tests cover the task lifecycle, capability matching, permission expiry and
revocation, the approval flow, emergency stop, and the HTTP and WebSocket
surface.
