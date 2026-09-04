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
