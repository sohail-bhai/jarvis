"""How the control plane actually talks to an agent.

An agent is a capability and an address, not a framework. The orchestrator
hands work to an adapter and gets text back; whether that ran in this process,
over HTTP, or inside a container is the adapter's business.

Keeping this seam narrow is what lets MCP, LangGraph or a Dockerised agent join
later without the orchestrator learning anything about them.
"""

import json
import logging
import urllib.error
import urllib.request

from assistant.control.models import StepResult

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 180


class AgentUnavailable(Exception):
    """The agent could not be reached or refused the work."""


class NativeAdapter:
    """Runs the step in this process, through the JARVIS agent loop.

    `token` lets the step stop between tool calls, and `authorize` decides per
    tool whether the capability behind it was actually granted.
    """

    framework = "native"

    def __init__(self, runner=None):
        self._runner = runner

    def run_step(self, instruction, context="", agent=None, token=None,
                 authorize=None, resolve_secrets=None):
        if self._runner is not None:
            return self._runner(instruction, context)

        # Imported late so the control plane stays importable without the
        # assistant's heavier runtime dependencies.
        from assistant import ai_brain

        return ai_brain.run_task_step(instruction, context=context,
                                      should_continue=token, authorize=authorize,
                                      resolve_secrets=resolve_secrets)


class HttpAdapter:
    """Posts the step to an agent that speaks HTTP.

    The contract is deliberately small - `{"instruction", "context"}` in,
    `{"output"}` out - so an agent written in any framework can satisfy it.
    """

    framework = "http"

    def __init__(self, transport=None, timeout=DEFAULT_TIMEOUT):
        self._transport = transport or _post_json
        self.timeout = timeout

    def run_step(self, instruction, context="", agent=None, token=None,
                 authorize=None, resolve_secrets=None):
        # A remote agent never receives resolved values: it gets the same
        # references, and asks the control plane if it needs them.
        if token is not None and token.cancelled:
            raise AgentUnavailable("Stopped before the agent was called.")

        endpoint = getattr(agent, "endpoint", "")
        if not endpoint:
            raise AgentUnavailable("This agent has no endpoint to call.")

        try:
            response = self._transport(
                endpoint, {"instruction": instruction, "context": context},
                self.timeout)
        except Exception as error:
            raise AgentUnavailable(f"Could not reach {endpoint}: {error}") from error

        if not isinstance(response, dict):
            raise AgentUnavailable("The agent replied with something unreadable.")
        if response.get("error") and response.get("ok") is not False:
            # An error with no `ok: false` means the call itself failed.
            raise AgentUnavailable(str(response["error"]))

        # A remote agent may answer with artifacts, or say it could not do the
        # work; both come back as a StepResult rather than bare text.
        return StepResult.of({
            "ok": response.get("ok", True),
            "output": response.get("output", ""),
            "artifacts": response.get("artifacts", []),
            "error": response.get("error", ""),
        })


def _post_json(url, payload, timeout):
    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class AdapterRegistry:
    """Maps an agent's framework onto the adapter that can drive it."""

    def __init__(self, default=None):
        self._adapters = {}
        self.default = default or NativeAdapter()
        self.register(self.default)
        self.register(HttpAdapter())

    def register(self, adapter, framework=None):
        self._adapters[framework or adapter.framework] = adapter
        return adapter

    def for_agent(self, agent):
        """The adapter for this agent, falling back to running it locally."""
        if agent is None:
            return self.default
        return self._adapters.get(agent.framework, self.default)

    def frameworks(self):
        return sorted(self._adapters)
