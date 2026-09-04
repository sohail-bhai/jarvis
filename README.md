# JARVIS Desktop Assistant - Version 1.2

> **Vision:** A project to build a self-learning, local AI agent assistant capable of autonomously controlling the laptop (clicking, typing, opening/closing apps) without relying on external cloud APIs for its core "thinking" capabilities.

Version 1.2 adds `config.json`, so you can customize JARVIS without editing Python code.

## Main Features

- First CustomTkinter desktop dashboard foundation
- Voice input and voice output
- Open apps and websites
- Google search and YouTube search
- Time, date, battery
- Screenshot
- Exact Windows volume control
- Notes
- Shutdown/restart confirmation
- Config-based personalization

## config.json

You can edit this file:

```json
{
    "user_name": "Sohail",
    "assistant_name": "Jarvis",
    "voice_rate": 170,
    "voice_volume": 1.0,
    "default_volume_step": 5,
    "listen_timeout_seconds": 8,
    "listen_phrase_time_limit_seconds": 25,
    "listen_pause_threshold_seconds": 2.0,
    "normal_pause_seconds": 2.0,
    "notes_pause_seconds": 3.0
}
```

## Voice Settings Commands

```text
what is my name
what is your name
change my name to Sohail
change your name to Friday
```

## Volume Commands

```text
volume down
volume up
volume down 20
volume up 20
volume 40
set volume to 40
mute volume
```

## Run

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Control Plane API

JARVIS coordinates work through a control plane: goals become tasks with
readable steps, AI helpers are chosen by what they can do, access is
time-limited, and consequential actions wait for your approval.

It is exposed over HTTP and WebSockets so the desktop app (Windows, macOS and
Linux) and the mobile client share one source of truth.

```bash
python -m assistant.api                 # localhost only
python -m assistant.api --host 0.0.0.0  # reachable from a phone
```

Interactive API documentation: `http://127.0.0.1:8765/docs`

Tasks are not just tracked, they are worked. Post a goal with `"run": true`,
or `POST /api/tasks/{id}/run`, and JARVIS carries out each step with the same
tools and safety guard as the voice loop, reporting progress over
`/ws/activity`:

```bash
curl -X POST localhost:8765/api/tasks \
     -H 'Content-Type: application/json' \
     -d '{"goal": "Summarise my notes", "steps": ["Reading notes"], "run": true}'
```

Remote clients pair once and then carry a device token:

```bash
curl -X POST localhost:8765/api/pair/code        # on this computer
curl -X POST http://<computer>:8765/api/pair \
     -H 'Content-Type: application/json' \
     -d '{"code": "418302", "name": "My phone", "kind": "phone"}'
```

> `--host 0.0.0.0` lets your network reach this computer. Callers still need a
> paired token, but only use it on a network you trust.

See [docs/control-plane.md](docs/control-plane.md) for the data model,
the full endpoint list, and known limitations.

## Safe Development Modes

Normal live voice assistant:

```bash
python main.py
```

Listen for one microphone command, execute it, then exit:

```bash
python main.py --once
```

Run one text command without using the microphone:

```bash
python main.py --text "time"
```

Run one text command without microphone or text-to-speech:

```bash
python main.py --text "time" --no-speech
```

Run safe command-router checks with desktop side effects stubbed:

```bash
python main.py --smoke-test
```

For automated checks, prefer:

```bash
python -m compileall -q main.py assistant gui jarvis_gui.py
python main.py --smoke-test
```

## Desktop GUI

Install dependencies first:

```bash
pip install -r requirements.txt
```

Launch the CustomTkinter dashboard:

```bash
python jarvis_gui.py
```

You can also launch it through the main entry point:

```bash
python main.py --gui
```

The dashboard does not start microphone listening automatically. Use **Start Listening** inside the window for voice mode, or use the text command field for one command at a time.

## If PyAudio Fails

```bash
pip install pipwin
pipwin install pyaudio
```

## If Screenshot Fails

```bash
pip install --upgrade pillow pyscreeze pyautogui
```
