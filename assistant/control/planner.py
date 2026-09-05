"""Turns a goal in the user's words into steps a person can watch.

The user says "prepare my project for deployment". This is what decides that
means analysing the repository, running the tests, building, deploying and
checking health - and which of those can happen at the same time.

The model call is injectable, so planning is tested without a local model and
a different model can be used later without touching the orchestrator.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)

# Enough steps to be useful, few enough to stay readable on a phone.
MAX_STEPS = 8

PLANNING_PROMPT = """Break this goal into at most {limit} steps.

Goal: {goal}

Rules:
- Each label is what VAVE will DO, phrased for a person watching:
  "Finding the relevant files", not "file_search()".
- List `depends_on` as the indexes of steps that must finish first. Steps with
  no dependencies run at the same time, so leave it empty where work really is
  independent.
- No step for asking the user, and no step for reporting back at the end.

Answer with JSON only, in this shape:
[{{"label": "Finding the relevant files", "depends_on": []}},
 {{"label": "Running the tests", "depends_on": [0]}}]
"""


class Planner:
    """Plans a goal into steps. Falls back to one step when planning fails."""

    def __init__(self, ask=None, max_steps=MAX_STEPS):
        self._ask = ask
        self.max_steps = max_steps

    def plan(self, goal):
        """Return a list of step dicts. Never raises, never returns nothing."""
        try:
            reply = self._ask_model(
                PLANNING_PROMPT.format(goal=goal, limit=self.max_steps))
        except Exception:
            logger.exception("Planning failed for %r", goal)
            return [{"label": goal, "depends_on": []}]

        steps = self._parse(reply)
        return steps or [{"label": goal, "depends_on": []}]

    def _ask_model(self, prompt):
        if self._ask is not None:
            return self._ask(prompt)

        # Imported late so the control plane stays importable without the
        # assistant's heavier runtime dependencies.
        from assistant.ai_brain import query_local_llm_chat
        from assistant.config import get_setting

        message = query_local_llm_chat(
            [{"role": "user", "content": prompt}],
            model=get_setting("llm_model", "qwen2.5:3b"), tools=False)
        if not message:
            raise RuntimeError("Could not reach the local model.")
        return message.get("content", "")

    def _parse(self, reply):
        """Read the model's answer defensively. Anything unusable is dropped."""
        payload = _first_json_array(reply or "")
        if payload is None:
            return []

        steps, count = [], 0
        for index, entry in enumerate(payload):
            if count >= self.max_steps:
                break

            label = (entry.get("label") if isinstance(entry, dict) else entry) or ""
            label = str(label).strip()
            if not label:
                continue

            depends_on = entry.get("depends_on", []) if isinstance(entry, dict) else []
            steps.append({
                "label": label,
                # A dependency may only point backwards, so a bad plan can
                # never produce a cycle or a step that waits on itself.
                "depends_on": sorted({
                    int(value) for value in depends_on or []
                    if isinstance(value, (int, float)) and 0 <= int(value) < index
                }),
            })
            count += 1

        return steps


def _first_json_array(text):
    """Models like to wrap JSON in prose or fences. Take the array out."""
    match = re.search(r"\[.*\]", text, re.S)
    if not match:
        return None
    try:
        payload = json.loads(match.group(0))
    except (ValueError, TypeError):
        return None
    return payload if isinstance(payload, list) else None
