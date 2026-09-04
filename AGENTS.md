# AGENTS.md

Guidance for future agents working in this repository.

## Project Scope

This is `JARVIS Desktop Assistant - Version 1.2`, a Python desktop assistant. It listens through the microphone, routes recognized voice commands, speaks responses with text-to-speech, and performs local desktop actions such as opening apps/websites, changing volume, taking screenshots, reading battery state, and managing notes.

JARVIS is evolving into a personal AI control plane: the user states a goal in
plain language, and JARVIS coordinates AI helpers, devices, Google Workspace,
files and the web behind the scenes.

The local AI brain is implemented, not a placeholder. `assistant/ai_brain.py`
runs an Ollama-backed agent loop with tool calling over roughly 57 registered
functions. Screen awareness, persistent vector memory, wake word, phone
bridging and the safety layer (guard, confirm, audit, overwatch) all exist.

Coordination lives behind a service boundary (`assistant/control/` and
`assistant/api.py`) so the desktop app and the separately built mobile client
share one source of truth. Do not put coordination logic in the UI.

Primary user-facing capabilities:

- Voice input and spoken output.
- CustomTkinter dashboard launched with `python jarvis_gui.py` or `python main.py --gui`.
- Config-based personalization through `config.json`.
- App launching for common local apps.
- Website opening and Google/YouTube search.
- Time, date, battery, screenshot, lock, shutdown, and restart commands.
- Exact Windows volume control through `pycaw`, with keyboard media-key fallback.
- Simple persistent notes stored in `data/notes.txt`.

## Repository Map

- `main.py`: application entry point. Creates `AssistantController` and starts it.
- `jarvis_gui.py`: CustomTkinter dashboard launcher. Shows a clear install message if `customtkinter` is missing.
- `gui/`: first desktop dashboard package. GUI widgets poll `EventBus` on the main thread and must not call CustomTkinter from worker threads.
- `gui/app.py`: dashboard window, worker-thread orchestration, event polling, text command handling, smoke-test button, and voice start/stop controls.
- `gui/theme.py`: shared dashboard colors and fonts.
- `gui/widgets/`: reusable dashboard panels.
- `assistant/controller.py`: reusable assistant loop for CLI now and a future GUI later. Manages assistant state, listening, command normalization, command dispatch, and event emission.
- `assistant/state.py`: central `AssistantState` enum for lifecycle states such as idle, listening, processing, speaking, error, and stopped.
- `assistant/events.py`: queue-based event bus and event objects for future GUI-safe polling.
- `assistant/text_utils.py`: conservative recognized-text normalization helpers.
- `assistant/commands.py`: central natural-language command router. This is where most new voice commands should be added.
- `assistant/speech.py`: speech recognition and text-to-speech setup. Keeps `speak()` and `listen()` available while lazily initializing microphone/TTS dependencies.
- `assistant/smoke_test.py`: safe command-router smoke checks with browser, app, note, screenshot, volume, and destructive system side effects stubbed.
- `assistant/system_tasks.py`: OS and hardware actions, including app launch, time/date/battery, screenshot, volume, lock, shutdown, and restart.
- `assistant/config.py`: config defaults, JSON loading/merging, and setting updates.
- `assistant/notes.py`: note capture, readback, and clearing.
- `assistant/ai_brain.py`: Ollama-backed agent loop (`_agent_loop`), the voice entry point `ask_ai()`, the control plane entry point `run_task_step()`, the tool-calling schema, and the `AVAILABLE_FUNCTIONS` tool registry.
- `assistant/control/`: the control plane. `models.py` (data model), `store.py` (SQLite), `service.py` (`ControlPlane` coordination logic), `executor.py` (`TaskExecutor`, which runs task steps through `ai_brain.run_task_step`).
- `assistant/api.py`: FastAPI HTTP + WebSocket boundary over the control plane. Run with `python -m assistant.api`.
- `assistant/memory.py`: persistent vector memory backed by ChromaDB.
- `assistant/swarm.py`: parallel sub-agents and actor-critic research.
- `assistant/vision.py`, `assistant/dev_tools.py`, `assistant/calendar_sync.py`, `assistant/email_tasks.py`, `assistant/telegram_sync.py`, `assistant/wakeword.py`, `assistant/interrupter.py`: screen OCR, developer automation, Google Calendar, mail, phone bridge, wake word, global interrupt hotkey.
- `assistant/guard.py`, `assistant/confirm.py`, `assistant/audit.py`, `assistant/overwatch/`: the safety layer. Preserve these.
- `docs/control-plane.md`: control plane architecture, endpoints and limitations.
- `config.json`: user-editable runtime config.
- `data/notes.txt`: user notes data file.
- `requirements.txt`: Python dependencies.
- `README.md`: user-facing setup and command examples.
- `.gitignore`: ignores local env, Python caches, `.env`, and generated screenshot PNGs.

Ignore these during code understanding unless a task specifically targets them:

- `venv/`: checked-in virtual environment; dependency code, not application source.
- `__pycache__/` and `*.pyc`: generated Python bytecode.
- `assets/screenshots/*.png`: generated screenshots from runtime use.

## Runtime Flow

1. `main.py` parses CLI mode flags.
2. Normal mode creates `AssistantController` and calls `run_forever()`.
3. `--text` calls `handle_text_command()` once without microphone input.
4. `--once` calls `run_once()` for one microphone command.
5. `--smoke-test` runs safe command-router checks with side effects stubbed.
6. `--gui` imports the GUI lazily and launches the CustomTkinter dashboard.
7. `AssistantController.run_forever()` sets the assistant to idle, greets the user, and starts the loop.
8. The controller calls `listen()` with configured timeout, phrase-time, and pause settings.
9. The controller normalizes recognized command text with `normalize_command_text()`.
10. If speech recognition returns a non-empty command string, `execute_command(command)` handles it.
11. `execute_command()` routes in this order:
   - stop/exit/goodbye words
   - settings commands
   - volume commands
   - configured website open commands
   - YouTube search
   - Google search
   - built-in app/system commands
   - notes commands
   - AI placeholder commands
   - fallback "I do not know this command yet."

Command text is lowercased and stripped in `listen()`, so command matching assumes lowercase input.

## Configuration

`assistant/config.py` owns defaults and merges them with `config.json`. Keep new user-tunable settings in both `DEFAULT_CONFIG` and `config.json` when appropriate.

Important settings:

- `user_name`, `assistant_name`
- `voice_rate`, `voice_volume`
- `default_volume_step`
- `listen_timeout_seconds`, `listen_phrase_time_limit_seconds`, `listen_pause_threshold_seconds`
- `normal_pause_seconds`, `notes_pause_seconds`
- `normal_max_phrase_time`, `notes_max_phrase_time`
- `websites`

The `websites` object supports config-driven additions. To add another site command without code changes, add an entry such as:

```json
"websites": {
    "docs": "https://example.com/docs"
}
```

Then saying `open docs` will route through `open_website()`.

## Adding Commands

Add most new command behavior in `assistant/commands.py`.

Recommended pattern:

1. Add a small helper function if the command has parsing or multiple aliases.
2. Call that helper early in `execute_command()` if it should take precedence.
3. Keep hardware/OS side effects in `assistant/system_tasks.py`.
4. Keep data persistence in the owning module, such as `assistant/notes.py` or `assistant/config.py`.
5. Always respond through `speak()` for user-visible outcomes.

Be careful with broad substring checks. For example, `elif "time" in command` can match unexpected phrases. Prefer explicit phrases or a helper when adding commands that may overlap with existing words.

## OS and Hardware Notes

The app is designed primarily for Windows, though `system_tasks.py` contains macOS and Linux branches for some actions.

Windows-specific behavior:

- Exact volume uses `pycaw` and `comtypes`.
- App launch commands use names such as `start chrome`, `notepad`, `calc`, `code`, `explorer`, and `start cmd`.
- Lock uses `ctypes.windll.user32.LockWorkStation()`.
- Shutdown/restart use `shutdown /s /t 5` and `shutdown /r /t 5`.

Risky actions already ask for spoken confirmation in `assistant/commands.py` before shutdown, restart, and clearing notes. Preserve confirmation behavior for destructive or disruptive commands.

Avoid running the full assistant casually in automation because normal mode starts the continuous voice loop, and `listen()` requires microphone access and internet access for Google speech recognition.

## Data and Generated Files

`data/notes.txt` is user data. Do not overwrite or clear it unless the task explicitly asks for that behavior.

Screenshots are saved to `assets/screenshots/`, which may not exist until runtime. That folder is generated by `take_screenshot()`.

`config.json` is user-editable state. Changes to names or assistant settings may be made by voice commands through `update_setting()`, so treat it as runtime state as well as project config.

## Dependencies and Setup

Use the README setup flow:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Dependencies include:

- `SpeechRecognition`
- `standard-aifc`
- `pyttsx3`
- `pyautogui`
- `pyscreeze`
- `pillow`
- `psutil`
- `PyAudio`
- `pycaw`
- `comtypes`
- `customtkinter`

PyAudio can be difficult to install on Windows. The README suggests `pipwin install pyaudio` if normal installation fails.

## Verification

There are small standard-library tests under `tests/`, plus a safe smoke-test CLI mode.

Low-risk syntax check:

```bash
python -m compileall -q main.py assistant gui jarvis_gui.py
```

Safe command-router smoke check:

```bash
python main.py --smoke-test
```

GUI launch for manual testing only:

```bash
python jarvis_gui.py
```

Do not run `python main.py` automatically during agent verification. It starts the continuous voice listening loop and can keep running or wait on microphone/TTS resources. For automated testing, use `compileall`, `--smoke-test`, or one-shot `--text "..." --no-speech` commands unless the user explicitly asks for a different runtime check.

Manual runtime check for the user:

```bash
python main.py
```

Manual runtime checks require a working microphone, speakers/TTS engine, and internet access for Google speech recognition. Give the user instructions instead of launching the assistant yourself. System commands can affect the local machine, so avoid casually testing shutdown, restart, lock, volume, and screenshot behavior without user intent.

## Current Limitations and Future Scope

Known limits in Version 1.2:

- No package metadata or installer.
- Command parsing is mostly substring matching, so overlapping phrases can misroute.
- `notes.py` assumes `data/` exists.
- Speech recognition depends on Google's online recognition service.
- Much of `system_tasks.py` is Windows-first. Volume control, lock, and window
  automation have no working Linux or macOS path, although the app targets all
  three. Platform-specific imports must stay lazy so the app still starts.
- The control plane has no authentication, so the API binds to localhost by
  default. See `docs/control-plane.md` for the full list of known gaps.
- Control plane steps run through `ai_brain.run_task_step()`, but a step that
  is already executing cannot be interrupted. Cancellation and emergency stop
  take effect between steps.
- Steps must be supplied by the caller. Nothing plans them from a goal yet.

Likely future work:

- Plan steps from a goal automatically instead of requiring the caller to list them.
- Give `system_tasks.py` real cross-platform implementations.
- Add authentication to the API before any remote use.
- Make command routing more structured to reduce accidental matches.
- Add safer abstractions around app launching and destructive system commands.

## GUI Development Rules

- Use `python jarvis_gui.py` for manual GUI work.
- Do not start microphone listening automatically from the GUI; the user must click Start Listening.
- GUI updates must happen on the CustomTkinter main thread. Worker threads should emit events through `EventBus`, then the app should poll with `after()`.
- Prevent duplicate listener threads. Start should be disabled while voice listening is active.
- Stop should be safe when the listener is inactive.
- Text command input should not require the microphone.
- Smoke Test in the GUI must use the safe existing smoke-test path and avoid real browser/app/volume/screenshot/destructive side effects.
- Keep GUI files modular under `gui/`; do not collapse everything into `main.py`.
- Do not add web frameworks, Electron, Node, or browser-based UI layers.

## Agent Working Rules

- Keep changes small and consistent with the existing plain-Python module style.
- Prefer `rg` for searching, and exclude `venv/`, `__pycache__/`, and generated screenshot files.
- Do not edit dependency files under `venv/`.
- Do not clear `data/notes.txt` or rewrite `config.json` unless the task requires it.
- Preserve confirmation prompts for destructive or disruptive actions.
- Do not run `python main.py` automatically; provide manual runtime instructions instead.
- Use `python -m compileall -q main.py assistant gui jarvis_gui.py` and `python main.py --smoke-test` for safe automated checks.
- Use `python main.py --text "time" --no-speech` for one-shot command checks.
- For GUI work, use `python jarvis_gui.py` manually and keep all widget updates on the main thread through EventBus polling.
- Use available Codex planning, implementation, review, and critique features when they help quality without expanding scope.
- Use `assistant.controller.AssistantController` as the integration point for assistant loops.
- Use `assistant.commands.execute_command()` as the main integration point for new voice command behavior.
- Keep platform-specific behavior isolated in `assistant/system_tasks.py`.
- Update `README.md` when user-facing commands, setup steps, or config keys change.

<!-- caveman-begin -->
Respond terse like smart caveman. All technical substance stay. Only fluff die.

Rules:
- Drop: articles (a/an/the), filler (just/really/basically), pleasantries, hedging
- Fragments OK. Short synonyms. Technical terms exact. Code unchanged.
- Pattern: [thing] [action] [reason]. [next step].
- Not: "Sure! I'd be happy to help you with that."
- Yes: "Bug in auth middleware. Fix:"

Switch level: /caveman lite|full|ultra|wenyan-lite|wenyan-full|wenyan-ultra
Stop: "stop caveman" or "normal mode"

Auto-Clarity: drop caveman for security warnings, irreversible actions, user confused. Resume after.

Boundaries: code/commits/PRs written normal.
<!-- caveman-end -->
