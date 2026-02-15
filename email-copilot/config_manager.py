import os
import json
from pathlib import Path
from typing import Optional, Dict

CONFIG_DIR = Path.home() / ".email-copilot"
CONFIG_FILE = CONFIG_DIR / "config.json"
SYSTEM_CONFIG_FILE = CONFIG_DIR / "system_config.json"

def ensure_config_dir():
    """Ensures the configuration directory exists."""
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def save_config(config_data: Dict[str, str]):
    """Saves user configuration data."""
    ensure_config_dir()
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=2)

def update_config_field(key: str, value: str):
    """Updates a single field in the user configuration."""
    config = load_config() or {}
    config[key] = value
    save_config(config)

def load_config() -> Optional[Dict[str, str]]:
    """Loads user configuration data."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def save_system_config(client_id: str, client_secret: str):
    """Saves system-level OAuth2 configuration."""
    ensure_config_dir()
    with open(SYSTEM_CONFIG_FILE, "w") as f:
        json.dump({"client_id": client_id, "client_secret": client_secret}, f, indent=2)

def load_system_config() -> Optional[Dict[str, str]]:
    """Loads system-level configuration, prioritizing environment variables."""
    # Check Environment Variables first (Zero-Tool Setup)
    env_id = os.getenv("GOOGLE_CLIENT_ID")
    env_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    if env_id and env_secret:
        return {"client_id": env_id, "client_secret": env_secret, "source": "environment"}

    # Fallback to local JSON file
    if SYSTEM_CONFIG_FILE.exists():
        try:
            with open(SYSTEM_CONFIG_FILE, "r") as f:
                config = json.load(f)
                config["source"] = "file"
                return config
        except Exception:
            return None
    return None

def is_app_configured() -> bool:
    """Checks if the system-level OAuth2 config is present."""
    config = load_system_config()
    return config is not None and "client_id" in config and "client_secret" in config

def is_configured() -> bool:
    """Checks if the required legacy configuration fields are present."""
    config = load_config()
    if not config:
        return False
    
    required_fields = ["IMAP_SERVER", "EMAIL_USER", "EMAIL_PASS", "SMTP_SERVER"]
    return all(config.get(field) for field in required_fields)
