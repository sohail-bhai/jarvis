import logging
logger = logging.getLogger(__name__)

import os
import platform
import subprocess
import datetime
from pathlib import Path

from assistant.speech import speak

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCREENSHOT_FOLDER = PROJECT_ROOT / "assets" / "screenshots"


def _get_pyautogui():
    import pyautogui
    pyautogui.FAILSAFE = False
    return pyautogui


def _get_psutil():
    import psutil
    return psutil

def get_os():
    return platform.system().lower()

def clamp_number(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, int(value)))

_STARTAPPS_CACHE = None
_STARTAPPS_CACHE_TIME = 0

def _get_windows_start_apps():
    """Cache and return all registered Windows Store & desktop applications."""
    global _STARTAPPS_CACHE, _STARTAPPS_CACHE_TIME
    import time
    import json
    now = time.time()
    if _STARTAPPS_CACHE is not None and (now - _STARTAPPS_CACHE_TIME) < 300:
        return _STARTAPPS_CACHE

    apps = []
    try:
        out = subprocess.check_output(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", "Get-StartApps | ConvertTo-Json"],
            timeout=5
        ).decode("utf-8", errors="ignore")
        data = json.loads(out)
        apps = data if isinstance(data, list) else [data]
    except Exception as e:
        logger.debug(f"Get-StartApps lookup note: {e}")

    _STARTAPPS_CACHE = apps
    _STARTAPPS_CACHE_TIME = now
    return apps

def _find_installed_app(query, system):
    """
    Search installed desktop applications on Windows, macOS, or Linux.
    Returns (path, display_name) or (None, None).
    """
    clean_q = query.lower().replace(" ", "").replace("_", "").replace("-", "")

    if system == "windows":
        # 1. Search Windows Store / UWP & desktop applications via Get-StartApps
        try:
            start_apps = _get_windows_start_apps()
            bad_startapp_words = {"uninstall", "remove", "setup", "reset", "documentation", "help", "readme"}

            # Exact normalized match
            for item in start_apps:
                raw_name = item.get("Name", "")
                name = raw_name.lower()
                if not any(bw in name for bw in bad_startapp_words):
                    if clean_q == name.replace(" ", "").replace("_", "").replace("-", ""):
                        return f"shell:AppsFolder\\{item['AppID']}", raw_name

            # Word match
            for item in start_apps:
                raw_name = item.get("Name", "")
                name = raw_name.lower()
                if not any(bw in name for bw in bad_startapp_words):
                    words = name.replace("_", " ").replace("-", " ").split()
                    if query.lower() in words or any(w.startswith(query.lower()) for w in words):
                        return f"shell:AppsFolder\\{item['AppID']}", raw_name

            # Substring match
            for item in start_apps:
                raw_name = item.get("Name", "")
                name = raw_name.lower()
                if not any(bw in name for bw in bad_startapp_words):
                    if query.lower() in name:
                        return f"shell:AppsFolder\\{item['AppID']}", raw_name
        except Exception as e:
            logger.debug(f"StartApps matching note: {e}")

        # 2. Search Start Menu .lnk shortcuts
        try:
            import winreg
        except ImportError:
            winreg = None

        dirs = [
            os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        ]
        candidates = []
        bad_words = {"uninstall", "remove", "setup", "reset", "documentation", "help", "readme", "website", "update"}

        for folder in dirs:
            if os.path.exists(folder):
                for root, _, files in os.walk(folder):
                    for f in files:
                        if f.lower().endswith(".lnk"):
                            name = f[:-4].lower()
                            if not any(bw in name for bw in bad_words):
                                candidates.append((name, os.path.join(root, f), f[:-4]))

        # Exact normalized match
        for name, path, orig in candidates:
            if clean_q == name.replace(" ", "").replace("_", "").replace("-", ""):
                return path, orig

        # Word-in-name match
        for name, path, orig in candidates:
            words = name.replace("_", " ").replace("-", " ").split()
            if query.lower() in words or any(w.startswith(query.lower()) for w in words):
                return path, orig

        # Substring match
        for name, path, orig in candidates:
            if query.lower() in name:
                return path, orig

        # Registry App Paths
        if winreg:
            for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                try:
                    with winreg.OpenKey(hive, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths") as key:
                        num = winreg.QueryInfoKey(key)[0]
                        for i in range(num):
                            sub = winreg.EnumKey(key, i)
                            clean = sub.lower().replace(".exe", "")
                            if clean == clean_q or query.lower() in clean:
                                val = winreg.QueryValue(key, sub)
                                if val and os.path.exists(val):
                                    return val, clean.title()
                except Exception:
                    pass

    elif system == "darwin":
        for app_dir in ["/Applications", os.path.expanduser("~/Applications")]:
            if os.path.exists(app_dir):
                for item in os.listdir(app_dir):
                    if item.lower().endswith(".app"):
                        name = item[:-4].lower()
                        if query.lower() in name or clean_q in name.replace(" ", ""):
                            return os.path.join(app_dir, item), item[:-4]

    else:
        desk_dir = "/usr/share/applications"
        if os.path.exists(desk_dir):
            for item in os.listdir(desk_dir):
                if item.lower().endswith(".desktop") and query.lower() in item.lower():
                    return os.path.join(desk_dir, item), item[:-8]

    return None, None


def open_app(app_name):
    """
    3-tier smart application & website launcher:
    Tier 1: Built-in known app aliases.
    Tier 2: Search installed applications on local disk.
    Tier 3: Fallback to browser (configured websites or web search/URL).
    """
    import webbrowser
    import urllib.parse
    from assistant.config import get_setting

    system = get_os()
    raw_query = str(app_name).strip()
    query = raw_query.lower()
    if query.startswith("open "):
        query = query[5:].strip()

    display_name = query.replace("_", " ").title()

    try:
        # Tier 1: Built-in known app aliases
        if system == "windows":
            windows_apps = {
                "chrome": "start chrome",
                "google chrome": "start chrome",
                "notepad": "start notepad",
                "calculator": "start calc",
                "calc": "start calc",
                "vscode": "start code",
                "vs code": "start code",
                "code": "start code",
                "file_explorer": "start explorer",
                "file explorer": "start explorer",
                "explorer": "start explorer",
                "cmd": "start cmd",
                "terminal": "start cmd",
                "command prompt": "start cmd",
                "powershell": "start powershell",
                "paint": "start mspaint",
                "task manager": "start taskmgr",
                "taskmgr": "start taskmgr",
                "settings": "start ms-settings:",
                "edge": "start msedge",
                "microsoft edge": "start msedge",
                "word": "start winword",
                "excel": "start excel",
                "powerpoint": "start powerpnt",
            }
            if query in windows_apps:
                # If window is already open, activate it instead of launching a duplicate blank window
                try:
                    import uiautomation as auto
                    app_classes = {"notepad": "Notepad", "calculator": "ApplicationFrameWindow", "calc": "ApplicationFrameWindow"}
                    target_cls = app_classes.get(query)
                    if target_cls:
                        existing = auto.WindowControl(searchDepth=1, ClassName=target_cls)
                        if existing.Exists(0.3):
                            speak(f"Opening {display_name}")
                            existing.SetActive()
                            return True
                except Exception:
                    pass

                speak(f"Opening {display_name}")
                cmd = windows_apps[query]
                if not cmd.startswith("start "):
                    cmd = f"start {cmd}"
                os.system(cmd)
                return True

        elif system == "darwin":
            mac_apps = {
                "chrome": "open -a 'Google Chrome'",
                "notepad": "open -a TextEdit",
                "calculator": "open -a Calculator",
                "vscode": "open -a 'Visual Studio Code'",
                "file_explorer": "open .",
                "cmd": "open -a Terminal",
            }
            if query in mac_apps:
                speak(f"Opening {display_name}")
                os.system(mac_apps[query])
                return True

        else:
            linux_apps = {
                "chrome": "google-chrome",
                "notepad": "gedit",
                "calculator": "gnome-calculator",
                "vscode": "code",
                "file_explorer": "xdg-open .",
                "cmd": "gnome-terminal",
            }
            if query in linux_apps:
                speak(f"Opening {display_name}")
                subprocess.Popen(linux_apps[query], shell=True)
                return True

        # Tier 2: Search installed applications on local machine
        app_path, found_name = _find_installed_app(query, system)
        if app_path:
            speak(f"Opening {found_name}")
            if system == "windows":
                os.startfile(app_path)
            elif system == "darwin":
                subprocess.Popen(["open", app_path])
            else:
                subprocess.Popen([app_path], shell=True)
            return True

        # Tier 3: Fallback to opening in browser
        websites = get_setting("websites", {})
        if query in websites:
            speak(f"Opening {display_name} in browser.")
            webbrowser.open(websites[query])
            return True

        web_services = {
            "youtube": "https://www.youtube.com",
            "netflix": "https://www.netflix.com",
            "reddit": "https://www.reddit.com",
            "twitter": "https://twitter.com",
            "x": "https://x.com",
            "instagram": "https://www.instagram.com",
            "facebook": "https://www.facebook.com",
            "linkedin": "https://www.linkedin.com",
            "whatsapp": "https://web.whatsapp.com",
            "telegram": "https://web.telegram.org",
            "chatgpt": "https://chatgpt.com",
            "gemini": "https://gemini.google.com",
            "claude": "https://claude.ai",
            "spotify": "https://open.spotify.com",
            "github": "https://github.com",
            "gmail": "https://mail.google.com",
            "drive": "https://drive.google.com",
            "google drive": "https://drive.google.com",
            "maps": "https://maps.google.com",
            "google maps": "https://maps.google.com",
            "prime video": "https://www.primevideo.com",
            "amazon": "https://www.amazon.com",
            "twitch": "https://www.twitch.tv",
            "wikipedia": "https://www.wikipedia.org",
            "canva": "https://www.canva.com",
            "notion": "https://www.notion.so",
            "figma": "https://www.figma.com",
        }
        if query in web_services:
            speak(f"Opening {display_name} in browser.")
            webbrowser.open(web_services[query])
            return True

        if " " not in query and query.isalnum():
            url = f"https://www.{query}.com"
        else:
            url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"

        speak(f"Opening {display_name} in browser.")
        webbrowser.open(url)
        return True

    except Exception as error:
        speak(f"Could not open {display_name}.")
        logger.info("Error:", error)
        return False


def close_app(app_name):
    """
    Closes or terminates a running application by name.
    """
    clean_name = str(app_name).lower().strip().replace("close ", "").replace("kill ", "")
    display_name = clean_name.replace("_", " ").title()
    import psutil

    proc_map = {
        "notepad": ["notepad.exe"],
        "calculator": ["calculatorapp.exe", "calc.exe", "calculator.exe"],
        "calc": ["calculatorapp.exe", "calc.exe"],
        "chrome": ["chrome.exe"],
        "google chrome": ["chrome.exe"],
        "vscode": ["code.exe"],
        "vs code": ["code.exe"],
        "code": ["code.exe"],
        "discord": ["discord.exe"],
        "spotify": ["spotify.exe"],
        "netflix": ["netflix.exe"],
        "cmd": ["cmd.exe"],
        "terminal": ["windowsterminal.exe", "cmd.exe", "powershell.exe"],
        "edge": ["msedge.exe"],
        "brave": ["brave.exe"],
        "word": ["winword.exe"],
        "excel": ["excel.exe"],
        "powerpoint": ["powerpnt.exe"],
    }

    target_exes = [x.lower() for x in proc_map.get(clean_name, [f"{clean_name}.exe", clean_name])]
    closed = False

    for proc in psutil.process_iter(["name", "pid"]):
        try:
            p_name = proc.info["name"].lower()
            if p_name in target_exes or clean_name in p_name:
                proc.terminate()
                closed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if closed:
        speak(f"Closed {display_name}.")
        return f"Closed {display_name} successfully."
    else:
        speak(f"No running process found for {display_name}.")
        return f"No running process found for {display_name}."


def tell_time():
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    speak(f"The time is {current_time}")

def tell_date():
    current_date = datetime.datetime.now().strftime("%d %B %Y")
    speak(f"Today's date is {current_date}")

def search_web(query):
    """Searches the web for factual information."""
    try:
        import wikipedia
        return wikipedia.summary(query, sentences=3)
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Query is too ambiguous. Try one of these: {e.options[:3]}"
    except wikipedia.exceptions.PageError:
        pass
    except Exception:
        pass

    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            
        if not results:
            return "No results found on the web."
            
        summary = ""
        for i, r in enumerate(results):
            summary += f"Result {i+1}: {r['title']}\nSnippet: {r['body']}\n\n"
        return summary
    except Exception as e:
        return f"Error searching the web: {e}"

def get_weather(city):
    """Fetches the current live weather for a given city."""
    try:
        import requests
        # We use wttr.in because it is free and requires no API key.
        response = requests.get(f"https://wttr.in/{city}?format=j1", timeout=5)
        if response.status_code == 200:
            data = response.json()
            current = data['current_condition'][0]
            temp = current['temp_C']
            desc = current['weatherDesc'][0]['value']
            feels = current['FeelsLikeC']
            return f"The current weather in {city} is {desc} at {temp}°C, feels like {feels}°C."
        else:
            return f"Could not fetch weather for {city}. (Status code {response.status_code})"
    except Exception as e:
        return f"Error fetching weather: {e}"

def tell_battery():
    try:
        psutil = _get_psutil()
        battery = psutil.sensors_battery()

        if battery is None:
            speak("Battery information is not available.")
            return

        percent = battery.percent
        if battery.power_plugged:
            speak(f"Battery is at {percent} percent and charging.")
        else:
            speak(f"Battery is at {percent} percent.")

    except Exception as error:
        speak("Could not check battery status.")
        logger.info("Error:", error)

def take_screenshot():
    try:
        pyautogui = _get_pyautogui()
        SCREENSHOT_FOLDER.mkdir(parents=True, exist_ok=True)
        
        # Cleanup old screenshots (keep only the last 10)
        existing_shots = sorted(SCREENSHOT_FOLDER.glob("screenshot_*.png"), key=lambda p: p.stat().st_mtime)
        if len(existing_shots) >= 10:
            for old_shot in existing_shots[:-9]:
                try:
                    old_shot.unlink()
                except Exception:
                    pass

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        screenshot_path = SCREENSHOT_FOLDER / f"screenshot_{timestamp}.png"

        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_path)

        speak("Screenshot saved successfully.")
        logger.info(f"Saved at: {screenshot_path}")

    except Exception as error:
        speak("Could not take screenshot.")
        logger.info("Error:", error)

def get_windows_volume_controller():
    """
    Returns Windows system volume controller using pycaw.
    Supports both new and old pycaw versions.
    """

    if get_os() != "windows":
        return None

    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        device = AudioUtilities.GetSpeakers()

        # New pycaw method
        if hasattr(device, "EndpointVolume"):
            return device.EndpointVolume

        # Old pycaw method
        from ctypes import POINTER, cast
        from comtypes import CLSCTX_ALL

        interface = device.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )

        try:
            return interface.QueryInterface(IAudioEndpointVolume)
        except Exception:
            return cast(interface, POINTER(IAudioEndpointVolume))

    except Exception as error:
        logger.info("Windows volume controller error:", error)
        return None

def get_current_volume():
    volume = get_windows_volume_controller()

    if volume is None:
        return None

    try:
        return round(volume.GetMasterVolumeLevelScalar() * 100)
    except Exception as error:
        logger.info("Could not get current volume:", error)
        return None

def set_volume(level):
    level = clamp_number(level)
    volume = get_windows_volume_controller()

    if volume is not None:
        try:
            volume.SetMasterVolumeLevelScalar(level / 100, None)
            speak(f"Volume set to {level} percent.")
            return
        except Exception as error:
            logger.info("Could not set exact volume:", error)

    speak("Exact volume control is not available. Using keyboard volume keys instead.")
    pyautogui = _get_pyautogui()
    pyautogui.press("volumeup")

def change_volume_by(amount):
    current_volume = get_current_volume()

    if current_volume is not None:
        new_volume = clamp_number(current_volume + amount)
        set_volume(new_volume)
        return

    steps = abs(int(amount)) // 5
    steps = max(1, steps)

    if amount > 0:
        pyautogui = _get_pyautogui()
        for _ in range(steps):
            pyautogui.press("volumeup")
        speak(f"Volume increased by about {steps * 5} percent.")
    else:
        pyautogui = _get_pyautogui()
        for _ in range(steps):
            pyautogui.press("volumedown")
        speak(f"Volume decreased by about {steps * 5} percent.")

def mute_volume():
    pyautogui = _get_pyautogui()
    pyautogui.press("volumemute")
    speak("Volume mute toggled.")

def lock_laptop():
    system = get_os()

    try:
        if system == "windows":
            import ctypes
            speak("Locking laptop.")
            ctypes.windll.user32.LockWorkStation()

        elif system == "darwin":
            speak("Locking Mac.")
            os.system("/System/Library/CoreServices/Menu\\ Extras/User.menu/Contents/Resources/CGSession -suspend")

        else:
            speak("Locking system.")
            os.system("gnome-screensaver-command -l")

    except Exception as error:
        speak("Could not lock the laptop.")
        logger.info("Error:", error)

def shutdown_laptop():
    system = get_os()
    speak("Shutting down.")

    if system == "windows":
        os.system("shutdown /s /t 5")
    elif system == "darwin":
        os.system("sudo shutdown -h now")
    else:
        os.system("shutdown now")

def restart_laptop():
    system = get_os()
    speak("Restarting.")

    if system == "windows":
        os.system("shutdown /r /t 5")
    elif system == "darwin":
        os.system("sudo shutdown -r now")
    else:
        os.system("reboot")

def click_at(x, y):
    """Clicks at the specified X, Y coordinates."""
    pyautogui = _get_pyautogui()
    pyautogui.click(x=x, y=y)
    
def type_text(text):
    """Types the given text automatically."""
    pyautogui = _get_pyautogui()
    pyautogui.write(text, interval=0.01)
    
def press_key(key):
    """Presses a specific keyboard key (e.g., 'enter', 'tab', 'esc')."""
    pyautogui = _get_pyautogui()
    pyautogui.press(key)

def find_and_click_text(target_text):
    """
    Uses UIAutomation to find a button/text on the screen and clicks it.
    Returns True if found and clicked, False otherwise.
    """
    import uiautomation as auto
    import time
    
    logger.info(f"[JARVIS Vision] Searching entire desktop for '{target_text}'...")
    
    try:
        # Search the entire desktop tree up to depth 7 for the exact name
        btn = auto.Control(Name=target_text, searchDepth=7)
        if btn.Exists(3, 1): # wait up to 3 seconds
            btn.Click(simulateMove=False)
            time.sleep(1)
            return True
    except Exception as e:
        logger.info(f"[JARVIS Vision Error] {e}")
        
    speak(f"I could not find the text {target_text} on the screen.")
    return False

def read_screen(line_number=None, **kwargs):
    """Reads all visible text or a specific line from an open window or screen."""
    from assistant.vision import read_screen_text
    
    text = read_screen_text()
    if not text or not text.strip():
        return "No readable text found on the screen."
        
    lines = text.splitlines()
    if line_number is not None:
        try:
            idx = int(line_number)
            if 1 <= idx <= len(lines):
                target_line = lines[idx - 1].strip()
                if not target_line:
                    return f"Line {idx} is blank."
                return f"Line {idx}: {target_line}"
            else:
                return f"The document has {len(lines)} lines. Cannot read line {idx}."
        except (ValueError, TypeError):
            pass
            
    return f"Visible text on screen:\n{text}"

def write_to_screen_line(line_number: int, text: str):
    """
    Writes or appends text to a specific line in an open editor window (like Notepad).
    Uses UIAutomation ValuePattern directly on the active document, falling back to keyboard navigation.
    """
    import uiautomation as auto
    import time
    
    clean_text = str(text).strip()
    idx = int(line_number)
    
    # 1. Search candidate windows specifically for document/editor controls
    candidates = []
    fg = auto.GetForegroundControl()
    if fg and fg.ControlType == auto.ControlType.WindowControl:
        candidates.append(fg)
    for w in auto.GetRootControl().GetChildren():
        if w.ControlType == auto.ControlType.WindowControl and w not in candidates:
            candidates.append(w)

    def _get_doc_len(w):
        try:
            for ctrl, depth in auto.WalkControl(w, maxDepth=6):
                if ctrl.ControlType in (auto.ControlType.DocumentControl, auto.ControlType.EditControl) or ctrl.ClassName in ("RichEditD2DPT", "Edit"):
                    vp = ctrl.GetValuePattern()
                    if vp:
                        return len(vp.Value.strip())
        except Exception:
            pass
        return 0

    candidates.sort(key=_get_doc_len, reverse=True)

    for win in candidates:
        for ctrl, depth in auto.WalkControl(win, maxDepth=6):
            if ctrl.ControlType in (auto.ControlType.DocumentControl, auto.ControlType.EditControl) or ctrl.ClassName in ("RichEditD2DPT", "Edit"):
                try:
                    vp = ctrl.GetValuePattern()
                    if vp:
                        orig = vp.Value.replace("\r\n", "\n").replace("\r", "\n")
                        lines = orig.splitlines() if orig else []
                        
                        while len(lines) < idx:
                            lines.append("")
                            
                        if lines[idx - 1].strip():
                            lines[idx - 1] = f"{lines[idx - 1]} {clean_text}"
                        else:
                            lines[idx - 1] = clean_text
                            
                        new_content = "\r\n".join(lines)
                        vp.SetValue(new_content)
                        speak(f"Added '{clean_text}' on line {idx}.")
                        return f"Added '{clean_text}' on line {idx}."
                except Exception as e:
                    logger.debug(f"UIAutomation ValuePattern set failed: {e}")
                    
    # 2. Fallback: keyboard navigation
    try:
        pyautogui = _get_pyautogui()
        pyautogui.hotkey('ctrl', 'home')
        time.sleep(0.1)
        for _ in range(idx - 1):
            pyautogui.press('down')
        pyautogui.press('end')
        pyautogui.write(f" {clean_text}", interval=0.01)
        speak(f"Added '{clean_text}' on line {idx}.")
        return f"Added '{clean_text}' on line {idx}."
    except Exception as e:
        logger.warning(f"Keyboard fallback write failed: {e}")
        speak(f"Could not add text to line {idx}.")
        return f"Could not add text to line {idx}: {e}"

def analyze_screen(prompt, image_path=None):
    """Takes a screenshot and uses a local Vision AI to answer a question about the screen."""
    from assistant.vision import analyze_screen as vs_analyze
    return vs_analyze(prompt, image_path=image_path)

def propose_new_feature(feature_name, description):
    """
    Appends a requested feature to the project plan.md file.
    """
    try:
        from pathlib import Path
        plan_path = Path(__file__).resolve().parent.parent / "plan.md"
        
        if not plan_path.exists():
            return "Could not find plan.md"
            
        with open(plan_path, "a", encoding="utf-8") as f:
            f.write(f"\n### Auto-Requested: {feature_name}\n")
            f.write(f"- [ ] {description}\n")
            
        return f"Successfully added '{feature_name}' to the project plan."
    except Exception as e:
        return f"Failed to add feature to plan: {e}"


import datetime

def provide_morning_briefing():
    """
    On-Demand Morning Briefing.
    Fetches weather, schedule, and unread emails, then uses the local LLM to synthesize a natural greeting.
    """
    from assistant.speech import speak
    from assistant.config import get_setting
    from assistant.system_tasks import get_weather
    from assistant.calendar_sync import get_upcoming_events
    from assistant.email_tasks import read_unread_emails
    from assistant.ai_brain import query_local_llm_chat
    
    speak("Gathering your briefing data, sir.")
    
    # 1. Weather
    city = get_setting("default_location", "Hyderabad")
    weather_data = get_weather(city)
    
    # 2. Schedule
    schedule_data = get_upcoming_events(max_results=3)
    
    # 3. Emails
    try:
        email_data = read_unread_emails()
    except:
        email_data = "Failed to fetch emails."
        
    # 4. Synthesize with LLM
    user_name = get_setting("user_name", "Sir")
    time_str = datetime.datetime.now().strftime("%I:%M %p")
    
    prompt = f"""
You are JARVIS. It is currently {time_str}.
Your personality is a friendly buddy who has {user_name}'s back. You make funny jokes and use casual, conversational language instead of being a robotic servant.
Provide a concise, conversational morning briefing for {user_name} based on the following raw data.
Keep it strictly under 4 sentences. Speak naturally, throw in a quick joke, and do not list markdown bullets.

[Weather Data]: {weather_data}
[Schedule Data]: {schedule_data}
[Email Data]: {email_data}
"""

    response = query_local_llm_chat([{"role": "user", "content": prompt}], model=get_setting("llm_model", "qwen2.5:3b"))
    briefing = response.get("content", "") if isinstance(response, dict) else str(response)
    
    if briefing:
        speak(briefing)
        return briefing
    else:
        speak("I failed to compile your briefing.")
        return "Briefing compilation failed."


# ==========================================
# ATOMIC AGENTIC TOOLS (Mouse, Clipboard, Shell, File System)
# ==========================================

def scroll(clicks):
    """Scrolls the mouse wheel up (positive) or down (negative)."""
    import pyautogui
    try:
        pyautogui.scroll(clicks)
        return f"Scrolled {clicks} units."
    except Exception as e:
        return f"Scroll failed: {e}"

def drag_and_drop(start_x, start_y, end_x, end_y):
    """Drags the mouse from a start coordinate to an end coordinate."""
    import pyautogui
    try:
        pyautogui.moveTo(start_x, start_y)
        pyautogui.dragTo(end_x, end_y, duration=0.5)
        return f"Dragged from ({start_x},{start_y}) to ({end_x},{end_y})."
    except Exception as e:
        return f"Drag and drop failed: {e}"

def read_clipboard():
    """Reads text from the system clipboard."""
    import pyperclip
    try:
        content = pyperclip.paste()
        return content if content else "Clipboard is empty."
    except Exception as e:
        return f"Failed to read clipboard: {e}"

def write_clipboard(text):
    """Writes text to the system clipboard."""
    import pyperclip
    try:
        pyperclip.copy(text)
        return "Successfully copied to clipboard."
    except Exception as e:
        return f"Failed to write to clipboard: {e}"

def run_terminal_command(command):
    """Executes a background terminal command and returns the output."""
    import subprocess
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        output = result.stdout.strip()
        error = result.stderr.strip()
        if result.returncode == 0:
            return output if output else "Command executed successfully (no output)."
        else:
            return f"Command failed (Code {result.returncode}): {error}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 15 seconds."
    except Exception as e:
        return f"Failed to execute command: {e}"

def list_directory(path="."):
    """Lists files and folders in a given directory."""
    import os
    try:
        items = os.listdir(path)
        return "\n".join(items) if items else "Directory is empty."
    except Exception as e:
        return f"Failed to list directory: {e}"

def read_file(path):
    """Reads the contents of a local file."""
    import os
    try:
        if not os.path.exists(path):
            return "File not found."
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Failed to read file: {e}"

def write_file(path, content):
    """Writes text content to a local file (overwrites if exists)."""
    try:
        from pathlib import Path
        target_path = Path(path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {target_path}"
    except Exception as e:
        return f"Failed to write file: {e}"

def get_clickable_elements():
    """
    Scans the current active window and returns a list of clickable elements with their text and (x, y) coordinates.
    This solves the 'Coordinate Problem' for AI agents, allowing you to know exactly where to click without vision guessing.
    """
    try:
        import uiautomation as auto
        
        # We'll just scan the current active window to keep it fast
        active_window = auto.GetForegroundControl()
        if not active_window:
            for w in auto.GetRootControl().GetChildren():
                if w.ControlType == auto.ControlType.WindowControl and w.BoundingRectangle.width() > 100:
                    active_window = w
                    break
        if not active_window:
            active_window = auto.GetRootControl()
            
        elements = []
        # Walk through the control tree up to a certain depth to avoid hanging
        for control, depth in auto.WalkControl(active_window, maxDepth=4):
            # We look for things that might be clickable: Buttons, MenuItems, ListItems, Tabs, etc.
            if control.ControlType in (
                auto.ControlType.ButtonControl, 
                auto.ControlType.MenuItemControl,
                auto.ControlType.TabItemControl,
                auto.ControlType.ListItemControl,
                auto.ControlType.HyperlinkControl,
                auto.ControlType.EditControl
            ):
                name = control.Name
                rect = control.BoundingRectangle
                if name and rect.width() > 0 and rect.height() > 0:
                    # Calculate center point for clicking
                    center_x = rect.left + (rect.width() // 2)
                    center_y = rect.top + (rect.height() // 2)
                    elements.append(f"- '{name}': click_at(x={center_x}, y={center_y})")
        
        if not elements:
            return "Could not find any clearly named clickable buttons in the active window."
            
        return "Found these clickable elements:\n" + "\n".join(elements)
    except Exception as e:
        return f"Failed to get clickable elements: {e}"


def disable_voice_input():
    """Disables the wake word engine and microphone listening."""
    try:
        from assistant.wakeword import pause_wakeword
        from assistant.config import update_setting
        update_setting("wake_word_enabled", False)
        pause_wakeword()
        return "Microphone and wake word listening have been disabled."
    except ImportError:
        return "Wake word engine not found."

def enable_voice_input():
    """Enables the wake word engine and microphone listening."""
    try:
        from assistant.wakeword import resume_wakeword
        from assistant.config import update_setting
        update_setting("wake_word_enabled", True)
        resume_wakeword()
        return "Microphone and wake word listening have been enabled."
    except ImportError:
        return "Wake word engine not found."


def disable_speech_output():
    """Mutes JARVIS so he stops speaking out loud (Text-to-Speech). He will only reply via text."""
    from assistant.speech import set_speech_enabled
    from assistant.config import update_setting
    update_setting("speech_enabled", False)
    set_speech_enabled(False)
    return "My voice output has been disabled. I will only communicate via text."

def enable_speech_output():
    """Unmutes JARVIS so he speaks out loud again using Text-to-Speech."""
    from assistant.speech import set_speech_enabled
    from assistant.config import update_setting
    update_setting("speech_enabled", True)
    set_speech_enabled(True)
    return "My voice output has been enabled. I can speak again."


def send_telegram_update(message_text):
    """Sends a Telegram message to the user."""
    from assistant.config import get_setting
    from assistant.telegram_sync import send_telegram_message
    
    token = get_setting("telegram_bot_token", "")
    chat_id = get_setting("telegram_chat_id", "")
    
    if token.startswith("secret://"):
        try:
            from assistant.control.store import ControlStore
            from assistant.control.secrets import SecretStore, load_key
            store = ControlStore()
            secrets = SecretStore(store, key=load_key())
            token = secrets.resolve(token)
        except Exception:
            pass

    if not token or not chat_id:
        return "Telegram is not configured. Missing bot token or chat ID."
        
    send_telegram_message(token, chat_id, message_text)
    return f"Message sent to Telegram successfully: {message_text}"
