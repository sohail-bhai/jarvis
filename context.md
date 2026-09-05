# Project Context & Future Plans

## Vision
The ultimate goal of this project is to build a self-learning AI agent assistant named VAVE. 

Key characteristics of the final assistant:
- **Local Control:** Capable of interacting with the laptop locally (opening/closing apps, clicking, typing, etc.).
- **Local Thinking:** The "brain" of the AI will be built locally without relying on external cloud APIs (like Claude or OpenAI) for the core thinking and decision-making processes. It is intended to be a self-learning AI agent.
- **Current State:** Version 1.2 provides the foundation (desktop dashboard, voice recognition, basic system commands, configuration, and simple rule-based routing).

## Gap Analysis: Current System vs. True VAVE
- **Understanding:** We currently use rigid `if/else` substring matching. A true VAVE uses Natural Language Processing (NLP) to understand complex, multi-turn intents.
- **Action Space:** We currently run hardcoded OS scripts. A true VAVE can interact with any software by "seeing" the screen and using the mouse/keyboard programmatically.
- **Memory & Learning:** We currently have no memory between sessions. A true VAVE learns from mistakes and remembers user preferences permanently.
- **Privacy & Connectivity:** We currently rely on Google Speech Recognition (requires internet). A true VAVE processes voice, text, and thoughts entirely locally.

## Future Plan
The detailed roadmap to bridge these gaps is located in `plan.md`. It is divided into:
1. **Phase 1:** Local AI Brain & Natural Language Understanding (Major)
2. **Phase 2:** Autonomous UI Control & Screen Awareness (Major)
3. **Phase 3:** Long-Term Memory & Self-Learning (Major)
4. **Phase 4:** Quality of Life & Sensory Upgrades (Minor)

*Whenever a step is completed, `plan.md` will be updated with strikethroughs, and this `context.md` will be updated to reflect the new state of the system.*

## Current Progress
- **Phase 1, Step 1 (Completed):** Successfully integrated `ollama` as the local LLM engine in `ai_brain.py`. VAVE can now think locally without internet access for basic conversational requests.
- **Phase 1, Step 2 (Completed):** Refactored `commands.py` so any unrecognized voice command automatically falls back to the local LLM instead of failing.
- **Phase 1, Step 3 (Completed):** Upgraded `ai_brain.py` to use the `/api/chat` endpoint and implemented **Tool Calling**. The LLM can now autonomously decide to run python functions (e.g. `open_app`, `set_volume`, `search_google`) instead of just chatting.
- **Phase 1, Step 4 (Completed):** Added short-term conversation memory. VAVE now remembers the last 10 interactions in a session, allowing for follow-up questions and contextual awareness.
- **Phase 2, Step 1 & 2 (Completed):** Created `vision.py` using `pytesseract` to find exact pixel coordinates of text on the screen. Added PyAutoGUI tools (`type_text`, `press_key`, `find_and_click_text`) to `ai_brain.py` so the LLM can see and interact with the UI autonomously.
- **Phase 2, Step 3 (Completed):** Upgraded `ai_brain.py` with an **Agent Loop**. VAVE can now perform multi-step actions (e.g., calling a tool, checking the result, and deciding what to do next up to 5 times) before talking back to the user.
- **Phase 3, Step 1 & 2 (Completed):** Added `assistant/memory.py` leveraging a local `data/memory.json` store. Gave VAVE a `remember_fact` tool and injected the contents of `memory.json` into its System Prompt on startup for permanent long-term context.
- **Phase 3, Step 3 & 4 (Completed):** The memory context injection inherently resolves Step 3 and 4. The LLM can retrieve facts seamlessly, achieving the primary goal of self-learning and permanent state tracking without complex vector databases.
