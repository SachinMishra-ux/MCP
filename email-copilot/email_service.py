import os
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.header import decode_header
from typing import List, Optional
from models import EmailMetadata
from datetime import datetime
import oauth_manager
import config_manager

def get_resolve_email(creds=None) -> Optional[str]:
    """Resolves the email address to use for IMAP/SMTP."""
    # 1. Try config.json (persisted)
    config = config_manager.load_config()
    if config and config.get("EMAIL_USER"):
        return config["EMAIL_USER"]
    
    # 2. Try id_token (from current creds)
    if creds and creds.id_token:
        return creds.id_token.get('email')
        
    # 3. Fallback to Env
    return os.getenv("EMAIL_USER")

def get_unread_emails() -> List[EmailMetadata]:
    """Fetches up to 50 unread emails without marking them as read (using BODY.PEEK)."""
    creds = oauth_manager.load_credentials()
    if not creds:
        print("DEBUG: No credentials found for get_unread_emails")
        return []
        
    email_user = get_resolve_email(creds)
    print(f"DEBUG: Resolving IMAP for {email_user}")
    
    emails = []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        auth_string = oauth_manager.get_auth_string(email_user, creds.token)
        mail.authenticate('XOAUTH2', lambda x: auth_string)
        
        mail.select("inbox")
        
        status, messages = mail.search(None, 'UNSEEN')
        print(f"DEBUG: IMAP Search Status: {status}, Found messages: {len(messages[0].split())}")
        if status != 'OK':
            return []

        # Increase limit to 50 for much better visibility of the inbox
        for num in messages[0].split()[-50:]:
            # Use BODY.PEEK[] to avoid marking as SEEN
            res, msg_data = mail.fetch(num, "(BODY.PEEK[])")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    emails.append(_parse_email_message(response_part[1], num, email_user))
        mail.logout()
    except Exception as e:
        print(f"IMAP Error: {e}")
    
    return emails

def send_email_message(to_email: str, subject: str, body: str) -> bool:
    """Sends an email using the SMTP server and XOAUTH2."""
    creds = oauth_manager.load_credentials()
    if not creds:
        return False
        
    email_user = get_resolve_email(creds)
        
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = email_user
        msg['To'] = to_email
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            auth_string = oauth_manager.get_auth_string(email_user, creds.token)
            server.docmd('AUTH', 'XOAUTH2 ' + auth_string)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"SMTP Error: {e}")
        return False

def search_emails(query: str) -> List[EmailMetadata]:
    """Searches emails matching the query across all messages."""
    creds = oauth_manager.load_credentials()
    if not creds:
        return []
        
    email_user = get_resolve_email(creds)
    
    emails = []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        auth_string = oauth_manager.get_auth_string(email_user, creds.token)
        mail.authenticate('XOAUTH2', lambda x: auth_string)
        
        mail.select("inbox")
        
        # Using X-GM-RAW allowed for advanced Gmail search (same as search box)
        status, messages = mail.search(None, 'X-GM-RAW', f'"{query}"')
        if status != 'OK' or not messages[0]:
            # Fallback to standard if X-GM-RAW fails or is empty
            status, messages = mail.search(None, f'OR (SUBJECT "{query}") (TEXT "{query}")')
            
        if status != 'OK' or not messages[0]:
            return []

        # Get latest 10 matches for searching
        for num in messages[0].split()[-10:]:
            res, msg_data = mail.fetch(num, "(BODY.PEEK[])")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    emails.append(_parse_email_message(response_part[1], num, email_user))
        mail.logout()
    except Exception as e:
        print(f"Search Error: {e}")
    
    return emails

def get_email_by_id(email_id: str) -> Optional[EmailMetadata]:
    """Fetches a specific email by its UID directly."""
    creds = oauth_manager.load_credentials()
    if not creds:
        return None
        
    email_user = get_resolve_email(creds)
    
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        auth_string = oauth_manager.get_auth_string(email_user, creds.token)
        mail.authenticate('XOAUTH2', lambda x: auth_string)
        mail.select("inbox")
        
        res, msg_data = mail.fetch(email_id, "(BODY.PEEK[])")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                return _parse_email_message(response_part[1], email_id.encode(), email_user)
        mail.logout()
    except Exception as e:
        print(f"Fetch ID Error: {e}")
    return None

def save_draft_message(to_email: str, subject: str, body: str) -> bool:
    """Saves a draft email to the IMAP Drafts folder."""
    creds = oauth_manager.load_credentials()
    if not creds:
        return False
        
    email_user = get_resolve_email(creds)
    
    try:
        # Create the email message
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = email_user
        msg['To'] = to_email
        msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        
        raw_message = msg.as_bytes()
        
        # Connect and append to Drafts
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        auth_string = oauth_manager.get_auth_string(email_user, creds.token)
        mail.authenticate('XOAUTH2', lambda x: auth_string)
        
        # Gmail specific drafts folder
        drafts_folder = '"[Gmail]/Drafts"'
        status, response = mail.append(drafts_folder, None, None, raw_message)
        
        mail.logout()
        return status == 'OK'
    except Exception as e:
        print(f"Draft Save Error: {e}")
        return False

def _parse_email_message(raw_bytes: bytes, num: bytes, recipient: str) -> EmailMetadata:
    """Helper to parse raw email bytes into EmailMetadata model."""
    msg = email.message_from_bytes(raw_bytes)
    subject, encoding = decode_header(msg["Subject"])[0]
    if isinstance(subject, bytes):
        subject = subject.decode(encoding if encoding else "utf-8")
    
    sender = msg.get("From")
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True).decode(errors='ignore')
                break
    else:
        body = msg.get_payload(decode=True).decode(errors='ignore')
    
    summary = body[:200] + "..." if len(body) > 200 else body
    
    return EmailMetadata(
        id=str(num.decode()),
        thread_id=msg.get("Message-ID", "unknown"),
        subject=subject,
        sender=sender,
        recipient=recipient,
        timestamp=datetime.now(),
        summary=summary,
        is_unread=True # Conservative default
    )
