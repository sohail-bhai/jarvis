import logging
logger = logging.getLogger(__name__)

import json
import os
import threading
import time
import urllib.request
import urllib.parse
from assistant import call_context

from assistant.config import get_setting, update_setting
from assistant.commands import execute_command
from assistant.speech import speak

_telegram_thread = None
_telegram_active = False

# --- Cross-process singleton lock ---
# Prevents MKL/numpy-spawned child processes from starting a second Telegram
# poller and causing a 409 Conflict.
_LOCK_PATH = os.path.join(os.path.dirname(__file__), "..", "data", ".telegram.pid")

def _acquire_lock():
    """Return True only if THIS process owns the singleton lock."""
    lock_path = os.path.abspath(_LOCK_PATH)
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    my_pid = os.getpid()

    # Read existing lock
    try:
        with open(lock_path, "r") as f:
            existing_pid = int(f.read().strip())
        # Check if that PID is still alive
        try:
            import psutil
            if psutil.pid_exists(existing_pid) and existing_pid != my_pid:
                logger.debug(f"[Telegram] Singleton lock held by PID {existing_pid}. This child ({my_pid}) will not start a second poller.")
                return False
        except ImportError:
            # psutil not available: fall back to os.kill signal 0 trick
            try:
                os.kill(existing_pid, 0)
                if existing_pid != my_pid:
                    logger.debug(f"[Telegram] Singleton lock held by PID {existing_pid}. Skipping.")
                    return False
            except (ProcessLookupError, PermissionError):
                pass  # Dead process — stale lock, we can claim it
    except (FileNotFoundError, ValueError):
        pass  # No lock file or corrupt — we can claim it

    # Write our PID
    try:
        with open(lock_path, "w") as f:
            f.write(str(my_pid))
        return True
    except OSError:
        return False

def _release_lock():
    """Release the lock if we own it."""
    lock_path = os.path.abspath(_LOCK_PATH)
    try:
        with open(lock_path, "r") as f:
            existing_pid = int(f.read().strip())
        if existing_pid == os.getpid():
            os.remove(lock_path)
    except Exception:
        pass

def send_telegram_message(token, chat_id, text):
    if not text:
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        text_str = str(text)
        chunks = [text_str[i:i+4000] for i in range(0, len(text_str), 4000)]
        for chunk in chunks:
            data = urllib.parse.urlencode({'chat_id': chat_id, 'text': chunk}).encode('utf-8')
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=10) as response:
                pass
    except Exception as e:
        logger.info(f"[Telegram Error] Could not send message: {e}")

def _telegram_worker():
    global _telegram_active
    
    token = get_setting("telegram_bot_token", "")
    chat_id = get_setting("telegram_chat_id", "")
    
    if token.startswith("secret://"):
        try:
            from assistant.control.store import ControlStore
            from assistant.control.secrets import SecretStore, load_key
            store = ControlStore()
            secrets = SecretStore(store, key=load_key())
            token = secrets.resolve(token)
        except Exception as e:
            logger.warning(f"Could not resolve secret for Telegram token: {e}")
    
    if not token:
        logger.info("[VAVE] Telegram Bot Token not found in config. Remote execution disabled.")
        return
        
    logger.info(f"[VAVE] Connecting to Telegram Bot from PID {os.getpid()}...")
    
    # Pre-emptively delete any existing webhooks that might cause a 409 Conflict with getUpdates
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{token}/deleteWebhook", timeout=5)
    except Exception:
        pass
        
    offset = 0
    
    while _telegram_active:
        try:
            # Use Long Polling (timeout=30s) so it doesn't spam the API
            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={offset}&timeout=30"
            req = urllib.request.Request(url)
            
            with urllib.request.urlopen(req, timeout=40) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if result.get("ok"):
                    for update in result.get("result", []):
                        offset = update["update_id"] + 1
                        
                        message = update.get("message", {})
                        text = message.get("text", "")
                        sender_chat_id = str(message.get("chat", {}).get("id", ""))
                        
                        if text:
                            logger.info(f"\n[Telegram Message Received]: {text}")
                            
                            # Security Check: Only allow commands from the authorized chat ID
                            # If chat_id is empty in config, we authorize the first person who messages it!
                            if not chat_id:
                                logger.info(f"[VAVE] Saving new Telegram Chat ID: {sender_chat_id}")
                                update_setting("telegram_chat_id", sender_chat_id)
                                chat_id = sender_chat_id
                                send_telegram_message(token, chat_id, "VAVE Remote Link Established. I am ready for commands.")
                                continue
                                
                            if sender_chat_id == chat_id:
                                text_clean = text.strip()
                                text_lower = text_clean.lower()
                                
                                if text_lower in ["/start", "start"]:
                                    send_telegram_message(
                                        token,
                                        chat_id,
                                        "Greetings! VAVE Remote Link is active and connected to your desktop. How can I assist you, Sir?"
                                    )
                                    continue

                                if text_lower in ["/help", "help"]:
                                    send_telegram_message(
                                        token,
                                        chat_id,
                                        "VAVE Telegram Bridge Commands:\n"
                                        "- Ask any question (uses local Ollama AI brain)\n"
                                        "- 'time' or 'date' (check system clock)\n"
                                        "- 'battery' (hardware battery status)\n"
                                        "- 'take a note <text>' (save persistent note)\n"
                                        "- 'read notes' (view notes)\n"
                                        "- 'screenshot' (capture screen)\n"
                                        "- '/yes <id>' or '/no <id>' (security confirmations)\n"
                                        "- '/kill' (emergency kill switch)"
                                    )
                                    continue

                                if text_lower.startswith("/yes ") or text_lower.startswith("/no "):
                                    from assistant import confirm
                                    parts = text_lower.split(" ")
                                    if len(parts) >= 2:
                                        approved = text_lower.startswith("/yes")
                                        confirm.resolve(parts[1], approved)
                                        send_telegram_message(token, chat_id, "Confirmation received.")
                                    continue
                                if text_lower == "/kill":
                                    from assistant import guard
                                    guard.set_kill_switch(True)
                                    send_telegram_message(token, chat_id, "Kill switch activated.")
                                    continue
                                    
                                speak(f"Incoming remote command: {text_clean}")
                                def _run_remote_cmd(cmd_text, token, chat_id):
                                    call_context.set_origin("telegram")
                                    try:
                                        execute_command(cmd_text, auto_confirm=True)
                                    except Exception as ex:
                                        logger.error(f"Telegram command error: {ex}")
                                        speak(f"Error executing command: {ex}")
                                call_context.spawn_thread(target=_run_remote_cmd, args=(text_clean, token, chat_id), daemon=True)
                            else:

                                logger.info(f"[VAVE] Unauthorized access attempt from Chat ID: {sender_chat_id}")
                                
        except urllib.error.HTTPError as e:
            if e.code == 409:
                logger.info(f"[Telegram Error 409 Conflict]: Another VAVE process is already running and listening to this bot. Please close all other terminal windows running VAVE!")
                time.sleep(15) # Wait longer so it doesn't spam
            else:
                logger.info(f"[Telegram Network Error]: {e}")
                time.sleep(5)
        except urllib.error.URLError as e:
            # Network issue, wait and retry
            logger.info(f"[Telegram Network Error]: {e}")
            time.sleep(5)
        except Exception as e:
            logger.info(f"[Telegram Sync Error]: {e}")
            time.sleep(5)
            
        time.sleep(1)
    
    # Release the lock when the poller stops
    _release_lock()

def start_telegram_sync():
    global _telegram_thread, _telegram_active
    
    if not get_setting("telegram_bot_token", ""):
        return
    
    # Only one process may poll. Child processes spawned by numpy/MKL are blocked here.
    if not _acquire_lock():
        return
        
    _telegram_active = True
    
    if _telegram_thread is None or not _telegram_thread.is_alive():
        _telegram_thread = threading.Thread(target=_telegram_worker, daemon=True)
        _telegram_thread.start()

def stop_telegram_sync():
    global _telegram_active
    _telegram_active = False
    _release_lock()
