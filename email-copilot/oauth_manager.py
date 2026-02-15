import os
import json
from pathlib import Path
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from typing import Optional, Dict

import config_manager
from typing import Optional, Dict

# Configuration
CONFIG_DIR = Path.home() / ".email-copilot"
TOKEN_FILE = CONFIG_DIR / "token.json"

# Scopes for Gmail IMAP/SMTP
SCOPES = [
    'https://mail.google.com/',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

def ensure_config_dir():
    if not CONFIG_DIR.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def get_redirect_uri() -> str:
    """Returns the dynamic redirect URI based on environment."""
    base_url = os.getenv("APP_BASE_URL", "http://localhost")
    return f"{base_url.rstrip('/')}/oauth/callback"

def get_flow() -> Flow:
    """Creates a Flow object using system configuration."""
    sys_config = config_manager.load_system_config()
    if not sys_config:
        raise ValueError("Application not configured. Admin must run 'configure_mcp_app' first.")
        
    client_config = {
        "web": {
            "client_id": sys_config["client_id"],
            "client_secret": sys_config["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": [get_redirect_uri()]
        }
    }
    
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=get_redirect_uri()
    )

def get_authorization_url() -> str:
    """Generates the authorization URL for the user."""
    flow = get_flow()
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    return auth_url

def authorize_with_code(code: str) -> str:
    """Exchanges an authorization code for tokens and persists user identity."""
    flow = get_flow()
    flow.fetch_token(code=code)
    
    credentials = flow.credentials
    save_credentials(credentials)
    
    # Persist the email address so the application knows which inbox to open
    if credentials.id_token and 'email' in credentials.id_token:
        config_manager.update_config_field("EMAIL_USER", credentials.id_token['email'])
    
    return credentials.to_json()

def save_credentials(credentials: Credentials):
    """Saves credentials to the home directory."""
    ensure_config_dir()
    with open(TOKEN_FILE, 'w') as f:
        f.write(credentials.to_json())

def load_credentials() -> Optional[Credentials]:
    """Loads credentials from storage, refreshing if necessary."""
    if not TOKEN_FILE.exists():
        return None
        
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        save_credentials(creds)
        
    return creds

def get_auth_string(user: str, token: str) -> str:
    """Generates the SASL XOAUTH2 authentication string."""
    return f"user={user}\1auth=Bearer {token}\1\1"

def is_authenticated() -> bool:
    """Checks if the user has valid credentials."""
    creds = load_credentials()
    return creds is not None and creds.valid
