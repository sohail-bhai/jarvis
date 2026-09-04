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
| `assistant/control/adapters.py` | How the control plane talks to an agent: in-process, over HTTP, or something added later. |
| `assistant/control/capabilities.py` | The catalog of namespaced capabilities and the risk each one carries. |
| `assistant/control/policy.py` | `PolicyEngine` - allow, ask or deny, from risk defaults and stored rules. |
| `assistant/control/executor.py` | `TaskExecutor` - runs a task's steps through the AI brain and writes the outcomes back. |
| `assistant/api/app.py` | FastAPI HTTP + WebSocket boundary. |
| `assistant/api/auth.py` | Device pairing, token authentication and rate limiting. |
| `assistant/api/errors.py` | One error envelope for every failure. |

## Core concepts

**Task** — a goal in the user's own words, with ordered **steps** phrased so a
person can read them ("Finding relevant files"). Progress is derived from how
many steps are done, so no client has to compute it.

**Agent** (`Helper` in the code, `/api/agents` over HTTP) — an AI worker that
advertises capabilities and reports how it is doing. Callers ask for a
capability, never for an agent by name:

```python
plane.create_task("Look this up", capability="research")
```

An agent that is offline, disabled or quarantined is never selected.

Agents carry a version, an endpoint, free-form metadata, and health that is
observed rather than guessed - heartbeats say it is alive, while the success
and error counts and the latencies come from work that actually ran:

```python
plane.heartbeat(agent.id, latency_ms=250, ok=True)
plane.agent_health()
# [{"name": "Research agent", "status": "idle", "error_rate": 0.0,
#   "p95_latency_ms": 250, ...}]
```

An agent that has reported and then goes quiet for 90 seconds is marked
offline; one that has never reported is left alone, because silence from
something that never spoke proves nothing. Devices work the same way with a
five-minute window, and this computer is never swept offline.

**Adapters** — an agent is a capability and an address, not a framework.
`NativeAdapter` runs the step in this process through the JARVIS agent loop;
`HttpAdapter` posts `{"instruction", "context"}` to the agent's endpoint and
reads `{"output"}` back. An unknown framework falls back to running locally, so
MCP, LangGraph or a containerised agent can join later without the
orchestrator learning anything about them.

**Stopping an agent** — `plane.kill_helper(id)` cancels the task it was
working on, revokes every grant it holds, disables it and quarantines it, in
one step. Other agents' grants are untouched. Nothing is deleted: the timeline
still shows what it did before it was stopped. `set_helper_enabled(id, False)`
is the gentler version - no new work, history intact.

**Capability** — a namespaced thing an agent may ask to do, such as
`google.gmail.read`, `browser.navigate` or `gcp.cloud_run.deploy`. Every
capability carries a risk level, and unknown names are treated as critical so a
typo can never become quiet access. `assistant/control/capabilities.py` is the
catalog; the Phase 2 integrations key off these exact strings.

**Permission** — access scoped to a resource, a set of actions, a task and an
expiry. Grants are released automatically when their task finishes. An agent
never receives one as a side effect of asking: it holds a permission or it
holds nothing.

**Approval** — a consequential action held until the user decides. Requesting
one moves the task to `waiting_approval`; approving resumes it, declining
cancels it. An approval that carries a capability *is* the held grant:
approving releases exactly that access, so the decision and the permission are
one event rather than two that can drift apart.

**Execution** — the control plane records steps; `TaskExecutor` runs them. It
hands each step to `ai_brain.run_task_step()`, which uses the same tools and
safety guard as the voice loop, then records the outcome on the step. Later
steps are told what earlier ones produced. The runner is injectable, so the
coordination logic is testable without a local model and a remote helper can
be substituted later.

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

## Asking for access

```python
result = plane.request_capability("google.gmail.send", task_id=task.id,
                                  agent_id="mail-agent")

result["status"]     # granted | waiting | denied
result["permission"] # the grant, when granted
result["approval"]   # what the user must answer, when waiting
result["judgement"]  # the decision, its risk level and why
```

Risk decides the default: low and medium run, high and critical ask. Stored
rules override that wherever the user has an opinion:

```python
plane.add_policy_rule("gcp.*", "deny", reason="No cloud from this machine.")
plane.add_policy_rule("google.gmail.send", "allow", task_id=task.id)
```

The narrowest matching rule wins — an exact capability beats a `google.*`
namespace, which beats `*` — and a deny beats an allow of equal narrowness, so
a broad permit never quietly re-enables something specifically forbidden. Rules
can also target one agent or one task.

| Risk | Examples | Default |
| --- | --- | --- |
| `low` | `browser.navigate`, `web.search` | runs |
| `medium` | `google.drive.read`, `system.screen.read` | runs |
| `high` | `google.gmail.send`, `filesystem.write` | asks you |
| `critical` | `gcp.cloud_run.deploy`, `filesystem.delete` | asks you |

`TOOL_CAPABILITIES` maps the tools in `ai_brain.py` onto the same names, so the
voice path and an agent calling over HTTP are judged by one set of rules.

## Running a task

`TaskExecutor` works the steps for you. It stops for a pending approval,
stops for an emergency stop, checkpoints after every step, and records an
honest failure with the real reason rather than a silent success.

```python
from assistant.control import get_executor

executor = get_executor()

task = executor.start(
    "Summarise my notes",
    steps=["Reading notes", "Writing the summary"],
)

executor.wait(task.id, timeout=120)   # optional; work runs in the background
```

Over HTTP:

```bash
curl -X POST localhost:8765/api/tasks \
     -H 'Content-Type: application/json' \
     -d '{"goal": "Summarise my notes", "steps": ["Reading notes"], "run": true}'
```

Steps run one at a time on a background thread. An emergency stop cancels the
task at the next step boundary; it does not interrupt a tool call already in
flight.

## Running the API

```bash
python -m assistant.api                 # localhost only (default)
python -m assistant.api --host 0.0.0.0  # reachable from a phone
python -m assistant.api --port 8765
```

Interactive documentation is generated at `http://127.0.0.1:8765/docs`.

> Binding to `0.0.0.0` lets anything on your network control this computer.
> It is opt-in and logs a warning on startup. Remote clients must pair first.

## Pairing a device

Reaching the port is not the same as being allowed to use it. Every remote
client is a paired device holding its own token, and one token can be revoked
without disturbing the others.

```bash
# On the computer itself (or from an already paired device):
curl -X POST localhost:8765/api/pair/code
# {"code": "418302", "expires_in": 600}

# From the phone, once:
curl -X POST http://<computer>:8765/api/pair \
     -H 'Content-Type: application/json' \
     -d '{"code": "418302", "name": "My phone", "kind": "phone"}'
# {"device": {...}, "token": "..."}   <- shown once, never again

# Every call after that:
curl -H 'Authorization: Bearer <token>' http://<computer>:8765/api/status

# WebSockets carry the same authority, so they authenticate too:
ws://<computer>:8765/ws/activity?token=<token>
```

Only the SHA-256 hash of a token is stored, so the database is not a list of
working credentials. `DELETE /api/devices/{id}/token` revokes one device.

Callers from this machine are trusted without a token by default, which keeps
the desktop app working. Three settings in `config.json` control this:

| Setting | Default | Meaning |
| --- | --- | --- |
| `api_require_auth` | `true` | Demand a token from anyone not trusted. |
| `api_trust_localhost` | `true` | Treat callers on this machine as authorised. |
| `api_rate_limit_per_minute` | `120` | Requests allowed per device per minute. |

Going over the limit returns `429` with a `Retry-After` header.

## Errors

Every failure uses one envelope, so no client special-cases anything:

```json
{"error": {"status": 404, "kind": "not_found", "message": "No such task."}}
```

`kind` is one of `bad_request`, `unauthenticated`, `forbidden`, `not_found`,
`conflict`, `invalid_request`, `rate_limited`, `internal_error`. A `422` also
carries `fields`, naming what was wrong.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/pair/code` | Mint a one-time pairing code. Local callers and paired devices only. |
| `POST` | `/api/pair` | Trade a code for a device token. |
| `DELETE` | `/api/devices/{id}/token` | Revoke one device's access. |
| `GET` | `/health` | Liveness check. |
| `GET` | `/api/status` | Counts for a home or security screen. |
| `GET` | `/api/tasks` | List tasks. `?active_only=true` hides finished ones. |
| `POST` | `/api/tasks` | Create a task from a goal and its steps. |
| `GET` | `/api/tasks/{id}` | One task with steps, progress and current step. |
| `POST` | `/api/tasks/{id}/run` | Work the task's steps through the AI brain. Returns `202` as soon as work starts. |
| `POST` | `/api/tasks/{id}/steps/start` | Mark a step as being worked on. |
| `POST` | `/api/tasks/{id}/steps/finish` | Finish a step, optionally as failed. |
| `POST` | `/api/tasks/{id}/complete` | Complete a task with a summary. |
| `POST` | `/api/tasks/{id}/cancel` | Stop a task. |
| `GET` | `/api/capabilities` | The catalog, with risk levels. `?prefix=google.*` filters. |
| `POST` | `/api/capabilities/request` | Ask for access. Answers granted, waiting or denied. |
| `GET`/`POST` | `/api/policies` | List or add allow/ask/deny rules. |
| `DELETE` | `/api/policies/{id}` | Remove a rule. |
| `GET` | `/api/devices` | Known machines. |
| `GET`/`POST` | `/api/agents` | List or register AI agents. `/api/helpers` is the older name and still works. |
| `GET` | `/api/agents/health` | Status, error rate and slow-end latency per agent. |
| `GET` | `/api/agents/{id}` | One agent. |
| `POST` | `/api/agents/{id}/heartbeat` | Report alive, with optional `latency_ms` and `ok`. |
| `POST` | `/api/agents/{id}/enable` | Give this agent work again. |
| `POST` | `/api/agents/{id}/disable` | Stop giving it work, keep its history. |
| `POST` | `/api/agents/{id}/kill` | Stop it now: work, access and future requests. |
| `POST` | `/api/devices` | Register a device with its capabilities. |
| `POST` | `/api/devices/{id}/heartbeat` | A device reports that it is still here. |
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

## Schema migrations

`store.py` owns an ordered, named migration list and a `schema_version` table.
Schema changes go there rather than into `SCHEMA`, so an existing
`data/control.db` is upgraded in place instead of quietly missing columns.
Names are permanent: never renumber or reorder them.

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

- **Tokens do not expire.** A paired device stays paired until it is revoked.
  There is no refresh or rotation yet.
- **Rate limiting is per process.** Restarting the API resets every bucket.
- **Capabilities are brokered, not enforced at the call site.** An agent that
  ignores the answer and calls a tool directly is not stopped yet; wiring the
  broker into the tool loop is WP5.
- **Agent selection is a first match, not a scheduler.** It prefers idle then
  least-recently-used. There is no load balancing or cost awareness.
- **Health is swept on read, not by a timer.** An agent flips to `offline` the
  next time agents, devices or status are listed, not the moment it goes quiet.
- **Agents are not authenticated separately.** An agent calls through a paired
  device's token; there is no per-agent credential yet.
- **Steps are not planned automatically.** The caller supplies the steps. A
  goal with no steps is run as a single piece of work.
- **A running step cannot be interrupted.** Cancellation and emergency stop
  are honoured between steps, not inside a tool call that is already running.
- **Helpers are selected but not marked busy.** Execution does not yet set a
  helper to `working` or release it afterwards.
- **Checkpoints are stored but not yet replayed.** `save_checkpoint` persists
  state; automatic recovery onto another helper is not implemented.
- **Permission expiry is checked on read**, not by a background timer. A grant
  stops authorising the moment it lapses, but its stored status only flips to
  `expired` the next time permissions are listed or checked.

## Tests

```bash
python -m unittest discover -s tests
```

207 tests cover the task lifecycle, capability matching, permission expiry and
revocation, the approval flow, emergency stop, step execution, failure and
cancellation paths, pairing and token authentication, rate limiting, schema
migrations, the capability catalog, policy precedence, the broker's grant,
hold and refuse paths, agent registration, heartbeats and staleness, the kill
switch, the HTTP and native adapters, and the HTTP and WebSocket surface. The executor tests use an
injected runner, so none of them need Ollama.
