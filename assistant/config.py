import logging
logger = logging.getLogger(__name__)

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = PROJECT_ROOT / "config.json"

DEFAULT_CONFIG = {
    "user_name": "Sohail",
    "assistant_name": "Jarvis",
    "voice_rate": 170,
    "voice_volume": 1.0,
    "llm_model": "qwen2.5:3b",
    
    "telegram_bot_token": "",
    "telegram_chat_id": "",
    
    "email_address": "",
    "email_app_password": "",
    
    # Control plane API. Authentication is on by default; callers on this
    # machine are trusted so the desktop app keeps working without a token.
    "api_require_auth": True,
    "api_trust_localhost": True,
    "api_rate_limit_per_minute": 120,

    "default_volume_step": 5,
    "listen_timeout_seconds": 8,
    "listen_phrase_time_limit_seconds": 25,
    "listen_pause_threshold_seconds": 2.0,
    "normal_pause_seconds": 2.0,
    "notes_pause_seconds": 3.0,
    "normal_max_phrase_time": 25,
    "notes_max_phrase_time": 60,

    "websites": {
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "gmail": "https://mail.google.com",
        "github": "https://github.com",
        "chatgpt": "https://chatgpt.com",
        "whatsapp": "https://web.whatsapp.com",
        "whatsapp web": "https://web.whatsapp.com",
        "instagram": "https://www.instagram.com"
    },
    
    "routines": {
        "good morning": [
            "what time is it",
            "what is the battery percentage",
            "read my emails"
        ],
        "focus mode": [
            "set volume to 20",
            "open chatgpt"
        ]
    }
}

_config_cache = None
_config_mtime = 0

def create_default_config():
    CONFIG_FILE.write_text(
        json.dumps(DEFAULT_CONFIG, indent=4),
        encoding="utf-8"
    )

def deep_merge(base, override):
    merged = base.copy()
    for k, v in override.items():
        if isinstance(v, dict) and k in merged and isinstance(merged[k], dict):
            merged[k] = deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged

def load_config():
    global _config_cache, _config_mtime
    if not CONFIG_FILE.exists():
        create_default_config()

    try:
        current_mtime = os.path.getmtime(CONFIG_FILE)
        if _config_cache is not None and current_mtime == _config_mtime:
            return _config_cache

        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            user_config = json.load(file)

        _config_cache = deep_merge(DEFAULT_CONFIG, user_config)
        _config_mtime = current_mtime

        return _config_cache

    except Exception as error:
        logger.info("Config error:", error)
        logger.info("Using default config.")
        return DEFAULT_CONFIG

def save_config(config):
    CONFIG_FILE.write_text(
        json.dumps(config, indent=4),
        encoding="utf-8"
    )
    global _config_mtime
    _config_mtime = 0

def get_setting(key, default=None):
    config = load_config()
    return config.get(key, default)

def update_setting(key, value):
    config = load_config()
    config[key] = value
    save_config(config)
