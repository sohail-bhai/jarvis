"""Talking to a JARVIS control plane running on another computer.

The desktop app calls the control plane directly, which works only while the
app and the work are on the same machine. Two people cannot share that: a
laptop running the desktop app opens its own `data/control.db` and sees its own
tasks, so the person on the other machine is looking at a different world.

`RemoteControlPlane` is the same surface reached over HTTP instead. Point the
desktop app at the computer that does the work and it becomes a thin client:
the tasks, the timeline and the approvals are the ones on that computer, and so
are the agents doing the work.

It deliberately offers only what a client needs. Storage, policy, secrets and
execution stay on the computer that owns them - a client that could reach into
them would be a second control plane, which is the problem this avoids.
"""

import json
import logging
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from assistant.config import get_setting, update_setting
from assistant.control.models import ActivityEvent, EventType

logger = logging.getLogger(__name__)

# A request that is answered slowly is still answered; one that hangs is not.
TIMEOUT_SECONDS = 20

# How long to wait before trying a dropped event stream again, and the ceiling
# for that wait, so a computer that is switched off is not hammered.
FIRST_RETRY_SECONDS = 1
MAX_RETRY_SECONDS = 30


class RemoteError(RuntimeError):
    """The other computer refused, or could not be reached.

    Carries `kind` from the API's error envelope where there was one, so a
    caller can tell "pair again" from "try again".
    """

    def __init__(self, message, status=0, kind="unreachable"):
        super().__init__(message)
        self.status = status
        self.kind = kind

    @property
    def needs_pairing(self):
        return self.kind in ("unauthenticated", "forbidden")


def normalise_host(value):
    """Accept `host`, `host:port` or a full URL and return a base URL."""
    text = str(value or "").strip().rstrip("/")
    if not text:
        return ""
    if not text.startswith(("http://", "https://")):
        text = f"http://{text}"
    without_scheme = text.split("://", 1)[1]
    if ":" not in without_scheme.split("/", 1)[0]:
        text = f"{text}:8765"
    return text


def configured_server():
    """The computer this machine should work through, if it has been told one.

    `jarvis_server` in `config.json` is what turns the desktop app from the
    thing that does the work into a client of something that does.
    """
    return normalise_host(get_setting("jarvis_server", ""))


def is_remote():
    return bool(configured_server())


class RemoteControlPlane:
    """A control plane on another computer, reached over HTTP and WebSocket."""

    def __init__(self, host=None, token=None):
        self.host = normalise_host(host or get_setting("jarvis_server", ""))
        self.token = token if token is not None else get_setting("jarvis_server_token", "")

        if not self.host:
            raise ValueError("No JARVIS server configured.")

        self._subscribers = []
        self._lock = threading.Lock()
        self._stream = None
        self._stop_stream = threading.Event()

    # -- plumbing ----------------------------------------------------------

    def _call(self, method, path, body=None, timeout=TIMEOUT_SECONDS):
        url = f"{self.host}{path}"
        data = json.dumps(body).encode() if body is not None else None

        request = urllib.request.Request(url, data=data, method=method)
        request.add_header("Accept", "application/json")
        if data is not None:
            request.add_header("Content-Type", "application/json")
        if self.token:
            request.add_header("Authorization", f"Bearer {self.token}")

        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                text = response.read().decode()
                return json.loads(text) if text else None
        except urllib.error.HTTPError as error:
            raise self._from_http_error(error) from None
        except urllib.error.URLError as error:
            raise RemoteError(f"Could not reach JARVIS at {self.host}. ({error.reason})") from None

    @staticmethod
    def _from_http_error(error):
        """Turn the API's one error envelope into one exception."""
        status = error.code
        message = f"JARVIS answered {status}."
        kind = "internal_error"

        try:
            envelope = json.loads(error.read().decode()).get("error", {})
            message = envelope.get("message", message)
            kind = envelope.get("kind", kind)
        except Exception:
            pass

        return RemoteError(message, status=status, kind=kind)

    # -- connecting --------------------------------------------------------

    def health(self):
        """Is anything answering there at all? Needs no token."""
        return self._call("GET", "/health", timeout=6)

    def pair(self, code, name, kind="computer", platform=""):
        """Trade a code shown on the other computer for this machine's token.

        The token is stored in `config.json`, so the desktop app connects by
        itself next time.
        """
        answer = self._call("POST", "/api/pair", {
            "code": str(code).strip(),
            "name": name,
            "kind": kind,
            "platform": platform,
        })

        self.token = answer["token"]
        update_setting("jarvis_server", self.host)
        update_setting("jarvis_server_token", self.token)
        return answer

    # -- the surface the desktop app uses ----------------------------------

    def status(self):
        return self._call("GET", "/api/status")

    def list_tasks(self, limit=50, active_only=False):
        query = urllib.parse.urlencode({"limit": limit,
                                        "active_only": str(bool(active_only)).lower()})
        return self._call("GET", f"/api/tasks?{query}")

    def task_detail(self, task_id):
        return self._call("GET", f"/api/tasks/{task_id}")

    def create_task(self, goal, steps=None, capability="", run=False, autoplan=False):
        """Create a task on the other computer, and optionally start it there.

        The work runs where the tools, the files and the model are, which is the
        whole point: a laptop asking for a build does not need to be able to do
        the build.
        """
        return self._call("POST", "/api/tasks", {
            "goal": goal,
            "steps": list(steps or []),
            "capability": capability or "",
            "run": bool(run),
            "autoplan": bool(autoplan),
        })

    def plan(self, goal):
        """Break a goal into steps without committing to them."""
        return self._call("POST", "/api/tasks/plan", {"goal": goal})

    def run_task(self, task_id):
        return self._call("POST", f"/api/tasks/{task_id}/run")

    def cancel_task(self, task_id):
        return self._call("POST", f"/api/tasks/{task_id}/cancel")

    def list_events(self, limit=100, task_id="", types=None):
        query = {"limit": limit}
        if task_id:
            query["task_id"] = task_id
        if types:
            query["types"] = ",".join(types)
        return self._call("GET", f"/api/activity?{urllib.parse.urlencode(query)}")

    def list_approvals(self, pending_only=True):
        query = urllib.parse.urlencode({"pending_only": str(bool(pending_only)).lower()})
        return self._call("GET", f"/api/approvals?{query}")

    def resolve_approval(self, approval_id, approved):
        return self._call("POST", f"/api/approvals/{approval_id}",
                          {"approved": bool(approved)})

    def list_permissions(self, active_only=True):
        query = urllib.parse.urlencode({"active_only": str(bool(active_only)).lower()})
        return self._call("GET", f"/api/permissions?{query}")

    def list_devices(self):
        return self._call("GET", "/api/devices")

    def list_agents(self):
        return self._call("GET", "/api/agents")

    def emergency_stop(self):
        return self._call("POST", "/api/emergency-stop")

    def resume(self):
        return self._call("POST", "/api/resume")

    # -- events ------------------------------------------------------------

    def subscribe(self, callback):
        """Report events from the other computer as they happen.

        Matches `ControlPlane.subscribe`: the callback receives an
        `ActivityEvent` and the return value unsubscribes, so code that follows
        a task does not care which side of the network the work is on.
        """
        with self._lock:
            self._subscribers.append(callback)
            self._ensure_stream()

        def unsubscribe():
            with self._lock:
                if callback in self._subscribers:
                    self._subscribers.remove(callback)

        return unsubscribe

    def _ensure_stream(self):
        """Open the event stream once, however many listeners there are."""
        if self._stream is not None and self._stream.is_alive():
            return

        self._stop_stream.clear()
        self._stream = threading.Thread(target=self._follow_events,
                                        name="jarvis-remote-events", daemon=True)
        self._stream.start()

    def close(self):
        """Stop listening. The other computer carries on working."""
        self._stop_stream.set()

    def _follow_events(self):
        """Keep the event stream open, reconnecting when it drops.

        A laptop closes its lid and changes networks, so a dropped stream is
        normal rather than an error worth reporting to the user.
        """
        try:
            from websockets.sync.client import connect
        except ImportError:
            logger.info("No websockets library; falling back to polling the timeline.")
            self._poll_events()
            return

        wait = FIRST_RETRY_SECONDS
        seen = self._latest_event_id()

        while not self._stop_stream.is_set():
            try:
                with connect(self._socket_url(), open_timeout=10) as socket:
                    wait = FIRST_RETRY_SECONDS
                    while not self._stop_stream.is_set():
                        message = socket.recv(timeout=30)
                        event = _to_event(json.loads(message))
                        if event.id != seen:
                            self._publish(event)
            except TimeoutError:
                continue        # a quiet computer, not a broken one
            except Exception:
                if self._stop_stream.is_set():
                    return
                time.sleep(wait)
                wait = min(wait * 2, MAX_RETRY_SECONDS)

    def _poll_events(self):
        """Ask for new timeline entries when no socket library is installed."""
        seen = set()
        first = True

        while not self._stop_stream.is_set():
            try:
                for payload in reversed(self.list_events(limit=25)):
                    if payload["id"] in seen:
                        continue
                    seen.add(payload["id"])
                    # The first pass is history, not news.
                    if not first:
                        self._publish(_to_event(payload))
                first = False
            except RemoteError:
                pass            # try again on the next pass

            if len(seen) > 500:
                seen = set(list(seen)[-250:])

            self._stop_stream.wait(3)

    def _latest_event_id(self):
        """What was already on the timeline, so history is not replayed as news."""
        try:
            events = self.list_events(limit=1)
            return events[0]["id"] if events else ""
        except RemoteError:
            return ""

    def _socket_url(self):
        base = self.host.replace("http://", "ws://").replace("https://", "wss://")
        query = urllib.parse.urlencode({"token": self.token}) if self.token else ""
        return f"{base}/ws/events{'?' + query if query else ''}"

    def _publish(self, event):
        with self._lock:
            subscribers = list(self._subscribers)

        for callback in subscribers:
            try:
                callback(event)
            except Exception:
                # A broken listener must never derail the work being reported.
                logger.exception("Remote event listener failed")


def _to_event(payload):
    """Rebuild an ActivityEvent so listeners see one shape either way."""
    try:
        event_type = EventType(payload.get("type", "note"))
    except ValueError:
        event_type = EventType.NOTE

    return ActivityEvent(
        id=payload.get("id", ""),
        task_id=payload.get("task_id", ""),
        type=event_type,
        message=payload.get("message", ""),
        actor=payload.get("actor", "JARVIS"),
        device_id=payload.get("device_id", ""),
        timestamp=payload.get("timestamp", time.time()),
        metadata=payload.get("metadata", {}) or {},
        agent_id=payload.get("agent_id", ""),
        capability=payload.get("capability", ""),
        risk=payload.get("risk", ""),
        approval_id=payload.get("approval_id", ""),
        result=payload.get("result", ""),
    )


_remote = None
_remote_lock = threading.Lock()


def get_remote_plane():
    """The shared client for the configured server, or None when local."""
    global _remote

    if not is_remote():
        return None

    with _remote_lock:
        if _remote is None or _remote.host != configured_server():
            _remote = RemoteControlPlane()
        return _remote
