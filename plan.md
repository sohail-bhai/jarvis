# JARVIS Implementation Plan

This document outlines the detailed steps to bridge the gap between our current V1.2 (rule-based, rigid) and the ultimate JARVIS vision (autonomous, self-learning, locally intelligent, and screen-aware).

## 🛑 Major Changes

### Phase 1: Local AI Brain & Natural Language Understanding
*Goal: Move away from rigid `if/else` keywords to an intelligent local agent that understands complex requests.*
- [x] ~~**Step 1:** Integrate a local LLM engine (e.g., Ollama, Llama.cpp) into `assistant/ai_brain.py`.~~
- [x] ~~**Step 2:** Refactor `assistant/commands.py` to route unrecognized commands to the local LLM.~~
- [x] ~~**Step 3:** Implement "Tool Calling" for the local LLM, allowing the AI to intelligently decide when to trigger existing functions (like `set_volume` or `open_app`) based on intent rather than hardcoded keywords.~~
- [x] ~~**Step 4:** Add short-term conversation memory so JARVIS remembers the context of the current session.~~

### Phase 2: Autonomous UI Control & Screen Awareness
*Goal: Allow JARVIS to use the computer like a human (clicking, typing, reading the screen).*
- [x] ~~**Step 1:** Implement a screen-reading module (using OCR like Tesseract or a local Vision model) to let JARVIS "see" what is on the screen and identify clickable elements.~~
- [x] ~~**Step 2:** Expand the system tasks to include generic `pyautogui` actions: `click_element(x, y)`, `type_text(text)`, `scroll(direction)`.~~
- [x] ~~**Step 3:** Build a loop where JARVIS can: Look at the screen -> Decide next action -> Execute action -> Verify result.~~
- [x] ~~**Step 4:** Test with a complex multi-step task (e.g., "Jarvis, open Notepad, write a poem, and save it to the desktop").~~

### Phase 3: Long-Term Memory & Self-Learning
*Goal: JARVIS learns from corrections and remembers facts permanently.*
- [x] ~~**Step 1:** Set up a local vector database (like ChromaDB, FAISS, or a simple SQLite JSON store) for persistent memory storage.~~
- [x] ~~**Step 2:** Create a mechanism to store user preferences and explicit facts (e.g., "Jarvis, remember that my favorite color is red").~~
- [x] ~~**Step 3:** Implement a feedback loop: When the user corrects JARVIS, it saves the correction to memory and retrieves it next time a similar task is requested.~~
- [x] ~~**Step 4:** Modify the system prompt in `ai_brain.py` to always query the vector database for relevant past memories before acting.~~

---

## 🛠️ Minor Changes

### Phase 4: Quality of Life Upgrades
*Goal: Make JARVIS feel like a premium, privacy-focused assistant.*
- [x] ~~**Step 1:** Replace `pyttsx3` with a more natural sounding online TTS (Edge-TTS) and build an offline fail-safe fallback using Piper TTS.~~
- [x] ~~**Step 2:** Optimize the response latency by using smaller LLMs (qwen2.5:3b) and fast TTS.~~

### Phase 5: Strict Offline Patch (DEFERRED)
- [ ] **Step 1:** Replace Google Speech Recognition with an offline wake-word and STT engine (like Vosk or openWakeWord) for total privacy without internet.
- [x] ~~**Step 2:** Update the `CustomTkinter` GUI to display real-time agent states (e.g., "Listening...", "Thinking...", "Executing Action...") and show a live log of the LLM's thought process.~~
- [x] ~~**Step 3:** Add dynamic configuration commands so the user can ask JARVIS to change its own settings (which updates `config.json` automatically).~~

### Phase 6: Phone Notifications & Remote Execution
*Goal: Sync Android/iOS phone to JARVIS so he can read notifications AND accept remote commands from your phone to execute on the laptop.*
- [x] ~~**Step 1:** Install a connector app on the phone (e.g., Telegram Bot or Pushbullet).~~
- [x] ~~**Step 2:** Background thread to read incoming messages. If a message is a command (e.g., "Jarvis, lock laptop"), execute it locally.~~
- [x] ~~**Step 3:** Have JARVIS read out important phone notifications (WhatsApp, SMS) through the PC speakers.~~

### Phase 7: Hardcoded Model Switching
*Goal: Allow instant, reliable LLM model switching without routing through the LLM.*
- [x] ~~**Step 1:** Add a hardcoded regex intercept in `commands.py` (e.g., "switch model [name]") to update `config.json` instantly before the request ever reaches the AI brain. This ensures that even if a model is broken, you can safely switch to a working one.~~

---

## 🚀 Advanced Roadmap / Backlog

### Phase 8: True Vector Memory (RAG)
*Goal: Make JARVIS's memory infinitely scalable without slowing down his context window.*
- [x] ~~**Step 1:** Replace the flat `memory.json` list with a local Vector Database (e.g., FAISS or ChromaDB).~~
- [x] ~~**Step 2:** Use local embeddings to only inject the top 3 most relevant memories into the prompt based on the current conversation.~~

### Phase 9: Fast Offline Wake-Word (Hands-Free)
*Goal: Allow the user to activate JARVIS from across the room without clicking UI buttons.*
- [x] ~~**Step 1:** Integrate `openWakeWord` or `Porcupine` to listen silently in the background with ~0% CPU usage.~~
- [x] ~~**Step 2:** Automatically trigger the main listening loop when the wake-word is detected.~~

### Phase 10: Graceful Interruption (The "Shut Up" Feature)
*Goal: Give the user full control to halt runaway AI tasks.*
- [x] ~~**Step 1:** Implement a global hotkey (e.g., `Ctrl+Shift+Space`) using the `keyboard` module.~~
- [x] ~~**Step 2:** When pressed, instantly clear the threaded audio queue, halt any PyAutoGUI typing loops, and reset the AI Brain state.~~

### Phase 11: Screen Awareness (Local Vision)
*Goal: Give JARVIS eyes so he can understand what the user is looking at.*
- [x] ~~**Step 1:** Add a background screenshot capture tool using `Pillow` and `pyautogui`.~~
- [x] ~~**Step 2:** Pass the Base64 image to Ollama's local vision models (`llava` or `moondream`) so he can answer questions like "What game am I playing?"~~
- [x] ~~**Step 3:** Enable commands like "What am I looking at?" or "Read this error message".~~

### Phase 12: Routine Automation Engine
*Goal: Allow JARVIS to chain multiple hardcoded tools together based on a single intent.*
- [x] ~~**Step 1:** Create a new configuration file (`routines.json` or add to `config.json`) where users can define macros.~~


### Comprehensive System Audit: Edge Cases & Shortcomings

After a deep codebase review across all 12 Phases, I have identified 8 critical architectural flaws, race conditions, and edge cases that need to be addressed before JARVIS can be considered "Production Ready".

#### 1. Context Window Overflow (The "OOM" Crash)
- **Bug:** `ai_brain.py` keeps the last 10 messages in history. If `read_screen` returns a 5,000-word Wikipedia page, and `read_emails` returns 20 long emails, the context window easily exceeds 10,000 tokens. Ollama's default limit is 2,048 tokens. If exceeded, Ollama throws an `HTTP 400 Bad Request` or an Out Of Memory (OOM) error, and JARVIS crashes.
- **Proposed Fix:** Limit the character count of tool returns (e.g., truncate `read_screen` to 2000 chars), dynamically trim history based on total character length, and increase `num_ctx` in the Ollama payload to 8192.

#### 2. Wakeword Thread Collision (Audio Race Condition)
- **Bug:** The `_on_wakeword_detected` callback executes synchronously inside the background `openwakeword` thread. It calls `self.run_once()`, which locks the microphone via `SpeechRecognition`. If the user manually clicks "Start Listening" on the GUI at the exact same moment, PyAudio crashes because it cannot open the microphone stream twice simultaneously.
- **Proposed Fix:** `controller.py` must use a `threading.Lock()` around `self.run_once()`, or push a "START_LISTENING" event to the main queue rather than executing directly in the background thread.

#### 3. Telegram Thread Blocking (The Webhook Backlog)
- **Bug:** `telegram_sync.py` uses `execute_command` directly inside its polling loop. If a user texts 5 commands rapidly, the loop blocks for ~15-30 seconds while the LLM generates answers. This causes a massive backlog, delays telegram responses, and can cause API timeouts.
- **Proposed Fix:** Incoming Telegram commands should be pushed to a standard `queue.Queue()`, and a dedicated execution thread should pop and execute them sequentially.

#### 4. The "Silent" Offline Piper TTS Failure
- **Bug:** `speech.py` brilliantly falls back to local Piper TTS if the internet drops (Edge-TTS fails). However, it hardcodes the path to `data/voices/en_US-ryan-medium.onnx`. If the user never manually downloaded this model, it fails silently. JARVIS becomes completely mute offline.
- **Proposed Fix:** If the Piper `.onnx` file is missing, automatically download it on first boot, OR fallback to the built-in Windows `pyttsx3` robotic voice as a last-resort failsafe.

#### 5. Screenshot Storage Memory Leak
- **Bug:** `system_tasks.py -> take_screenshot()` saves a new timestamped PNG every time it is called. There is no cleanup logic. Over months of use, the `assets/screenshots/` folder will inflate to gigabytes of wasted hard drive space.
- **Proposed Fix:** Add a cleanup routine that deletes screenshots older than 7 days, or caps the directory to a maximum of 50 images.

#### 6. ChromaDB First-Run Offline Crash
- **Bug:** `memory.py` initializes `chroma_client.get_or_create_collection("jarvis_memory")` on import. By default, ChromaDB uses the `all-MiniLM-L6-v2` embedding model. On the very first run, it attempts to download this model from HuggingFace. If the user installs JARVIS and runs him offline on day one, it crashes instantly on boot.
- **Proposed Fix:** Wrap ChromaDB initialization in a `try/except` block and fallback to a graceful "Offline Memory Disabled" state if the model cannot be fetched.

#### 7. Infinite Tool Loops (The LLM Trap)
- **Bug:** In `ai_brain.py`, the `for step in range(5)` loop allows the LLM to call tools up to 5 times per turn. If the LLM hallucinates and calls the exact same tool with the exact same arguments 5 times in a row, JARVIS freezes for 30 seconds doing nothing, then gives up.
- **Proposed Fix:** Track previous tool calls in the loop. If the LLM repeats an identical tool call, force a hard exit from the loop and inject a system message: "You already tried that tool and it failed. Try something else."


### Comprehensive System Audit: Edge Cases & Shortcomings

After a deep codebase review across all 12 Phases, I have identified 8 critical architectural flaws, race conditions, and edge cases that need to be addressed before JARVIS can be considered "Production Ready".

#### 1. Context Window Overflow (The "OOM" Crash)
- **Bug:** `ai_brain.py` keeps the last 10 messages in history. If `read_screen` returns a 5,000-word Wikipedia page, and `read_emails` returns 20 long emails, the context window easily exceeds 10,000 tokens. Ollama's default limit is 2,048 tokens. If exceeded, Ollama throws an `HTTP 400 Bad Request` or an Out Of Memory (OOM) error, and JARVIS crashes.
- **Proposed Fix:** Limit the character count of tool returns (e.g., truncate `read_screen` to 2000 chars), dynamically trim history based on total character length, and increase `num_ctx` in the Ollama payload to 8192.

#### 2. Wakeword Thread Collision (Audio Race Condition)
- **Bug:** The `_on_wakeword_detected` callback executes synchronously inside the background `openwakeword` thread. It calls `self.run_once()`, which locks the microphone via `SpeechRecognition`. If the user manually clicks "Start Listening" on the GUI at the exact same moment, PyAudio crashes because it cannot open the microphone stream twice simultaneously.
- **Proposed Fix:** `controller.py` must use a `threading.Lock()` around `self.run_once()`, or push a "START_LISTENING" event to the main queue rather than executing directly in the background thread.

#### 3. Telegram Thread Blocking (The Webhook Backlog)
- **Bug:** `telegram_sync.py` uses `execute_command` directly inside its polling loop. If a user texts 5 commands rapidly, the loop blocks for ~15-30 seconds while the LLM generates answers. This causes a massive backlog, delays telegram responses, and can cause API timeouts.
- **Proposed Fix:** Incoming Telegram commands should be pushed to a standard `queue.Queue()`, and a dedicated execution thread should pop and execute them sequentially.

#### 4. The "Silent" Offline Piper TTS Failure
- **Bug:** `speech.py` brilliantly falls back to local Piper TTS if the internet drops (Edge-TTS fails). However, it hardcodes the path to `data/voices/en_US-ryan-medium.onnx`. If the user never manually downloaded this model, it fails silently. JARVIS becomes completely mute offline.
- **Proposed Fix:** If the Piper `.onnx` file is missing, automatically download it on first boot, OR fallback to the built-in Windows `pyttsx3` robotic voice as a last-resort failsafe.

#### 5. Screenshot Storage Memory Leak
- **Bug:** `system_tasks.py -> take_screenshot()` saves a new timestamped PNG every time it is called. There is no cleanup logic. Over months of use, the `assets/screenshots/` folder will inflate to gigabytes of wasted hard drive space.
- **Proposed Fix:** Add a cleanup routine that deletes screenshots older than 7 days, or caps the directory to a maximum of 50 images.

#### 6. ChromaDB First-Run Offline Crash
- **Bug:** `memory.py` initializes `chroma_client.get_or_create_collection("jarvis_memory")` on import. By default, ChromaDB uses the `all-MiniLM-L6-v2` embedding model. On the very first run, it attempts to download this model from HuggingFace. If the user installs JARVIS and runs him offline on day one, it crashes instantly on boot.
- **Proposed Fix:** Wrap ChromaDB initialization in a `try/except` block and fallback to a graceful "Offline Memory Disabled" state if the model cannot be fetched.

#### 7. Infinite Tool Loops (The LLM Trap)
- **Bug:** In `ai_brain.py`, the `for step in range(5)` loop allows the LLM to call tools up to 5 times per turn. If the LLM hallucinates and calls the exact same tool with the exact same arguments 5 times in a row, JARVIS freezes for 30 seconds doing nothing, then gives up.
- **Proposed Fix:** Track previous tool calls in the loop. If the LLM repeats an identical tool call, force a hard exit from the loop and inject a system message: "You already tried that tool and it failed. Try something else."

#### 8. Routines Break the "Ask for Confirmation" Rule
- **Bug:** We explicitly ordered the LLM to ALWAYS ask "Shall I proceed?" before executing tools. However, when a Routine runs (e.g. "Good Morning" -> ["read my emails"]), it passes the string to `ask_ai()`. The LLM receives it, deduces it needs the `read_unread_emails` tool, and asks "Shall I proceed?" instead of just doing it! This completely breaks the fluidity of hands-free routines.
- **Proposed Fix:** Add an `auto_confirm=True` flag to `ask_ai()` and `execute_command()`. When a routine passes a command, it strips the confirmation rule from the system prompt dynamically so JARVIS just executes the routine silently.


### Phase 13: Hackathon & Developer Mode
*Goal: Turn JARVIS into a genuine pair-programmer and hackathon copilot for coding, git workflows, and project research.*
- [ ] **Feature 1: Auto-Git Committer & Push.** "Jarvis, commit my changes" / "Jarvis, push my code". Scans git status & git diff, uses local LLM to generate concise, professional commit messages, runs `git add .`, `git commit`, and optionally `git push`.
- [ ] **Feature 2: Autonomous Deep Tester Agent.** "Jarvis, deep test the project". Dynamically swaps to `qwen3.5:9b`, acts as an autonomous QA agent looping through terminal start commands, opening Chrome, and using OCR/Vision to inspect the rendered UI. It iterates until satisfied, then writes a comprehensive `deep_test_report.md` without modifying any code.
- [ ] **Feature 3: Project Idea & Open-Source Reference Scraper.** "Jarvis, scrape for ideas" / "Jarvis, find templates for my project". Reads local project files (README.md, package.json, main docs), summarizes current stack/concept, searches the web for relevant open-source templates, libraries, and reference architectures, and provides actionable suggestions.
- [ ] **Feature 4: Deep Work / Hackathon Focus Mode.** "Jarvis, start deep work". Configures volume, sets focus timer, and logs session stats.

- [ ] **Feature 2:** Refactor deep_test_project into an active iteration loop that interacts with the DOM.

### Phase 14: Autonomous Browser QA (Playwright) (Completed)

*Goal: Integrate OAuth-based third-party services for daily schedule management and media control.*

### Phase 15: Google Calendar Integration
*Goal: Integrate OAuth-based Google Calendar for daily schedule management.*
- [ ] **Feature 1:** Google Calendar API (Read schedule, add events).


### Phase 16: On-Demand Briefing
*Goal: A 'Jarvis, brief me' command that safely reads out schedule, weather, and tasks without auto-triggering in public spaces.*

### Phase 17: Smart Home Architecture
*Goal: Control LG AC (via LG ThinQ API) and prepare Webhook architecture for the Atomberg Fan (requires an IR blaster hub).*

### Phase 18: Full Gmail Integration
*Goal: Upgrade email integration to actively compose and send emails via voice.*


### Phase 19: Local Document RAG (Textbook Reader)
*Goal: Give JARVIS the ability to ingest large PDFs, API docs, and textbooks so the user can ask specific context-aware questions about their college materials.*


### Phase 20: Deep Web Researcher
*Goal: Utilize atomic GUI tools (scroll, click, type) to allow JARVIS to autonomously navigate the web, research topics, and compile markdown reports without human intervention.*

### Phase 21: The Multi-Agent Swarm
*Goal: Refactor the AI Brain from a single LLM loop into a swarm architecture (Commander, Coder, Researcher) that work in parallel to solve complex tasks faster.*

### Phase 21 Architecture Notes:
- **Role Definition:** JARVIS will act as the Helper/Researcher/QA, not the primary Coder, due to local LLM parameter constraints. (Antigravity handles heavy coding).
- **Dynamic Spawning:** JARVIS will not have hardcoded agents. He will dynamically create sub-agents on the fly based on the number of parallel tasks requested.
- **Actor-Critic Refinement:** For complex tasks (like Deep Web Research), JARVIS will spawn a 'Critic Sub-Agent' to challenge his work. The main agent and the critic will iterate to improve quality (with a hard cap to prevent infinite loops) before presenting the final result to the user.
