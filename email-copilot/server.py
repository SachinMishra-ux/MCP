import os
import sys
from fastmcp import FastMCP
from models import EmailMetadata, DraftReply
import email_service
import memory
import config_manager
import oauth_manager
from typing import List

# Initialize FastMCP
mcp = FastMCP("Email Copilot")

@mcp.tool()
def get_auth_status() -> str:
    """Checks if the user is authenticated via OAuth2 or manual setup."""
    if oauth_manager.is_authenticated():
        creds = oauth_manager.load_credentials()
        email = (creds.id_token.get('email') if creds.id_token else None) or 'Connected Account'
        return f"Authenticated: Using Google OAuth2 for {email}."
    
    if not config_manager.is_app_configured():
        return "Not Ready: The Application itself hasn't been configured by an admin yet. Please ask the admin to run 'configure_mcp_app' or set GOOGLE_CLIENT_ID/SECRET env vars."
        
    sys_config = config_manager.load_system_config()
    source = "Environment Variables" if sys_config.get("source") == "environment" else "Admin Tool"
    return f"Ready to Login: Application is configured via {source}. Please use 'get_authorization_url' to sign in."

@mcp.tool()
def configure_mcp_app(client_id: str, client_secret: str) -> str:
    """ADMIN ONLY: Configure the MCP application with Google Cloud credentials."""
    config_manager.save_system_config(client_id, client_secret)
    return "Application successfully configured! End-users can now authenticate using 'get_authorization_url'."

@mcp.tool()
def get_authorization_url() -> str:
    """Generates the Google Sign-In URL for the user."""
    if not config_manager.is_app_configured():
        return (
            "Error: Application not configured.\n\n"
            "Administrator Action Required:\n"
            "1. Go to Google Cloud Console.\n"
            "2. Create an OAuth 2.0 Web Client ID.\n"
            "3. Run the 'configure_mcp_app' tool with your Client ID and Client Secret."
        )
    try:
        url = oauth_manager.get_authorization_url()
        return (
            f"Please visit this URL to securely sign in with Google: {url}\n\n"
            "After signing in, Google will provide an authorization code. "
            "Copy that code and use the 'authorize_with_code' tool to finish connecting your account."
        )
    except Exception as e:
        return f"Error generating auth URL: {str(e)}"

@mcp.tool()
def authorize_with_code(code: str) -> str:
    """Finalizes OAuth2 authentication using the provided code."""
    try:
        oauth_manager.authorize_with_code(code)
        return "Authentication successful! You can now use the email copilot tools."
    except Exception as e:
        return f"Authentication failed: {str(e)}"

@mcp.tool()
def setup_email_account(
    email_user: str,
    email_pass: str,
    imap_server: str = "imap.gmail.com",
    smtp_server: str = "smtp.gmail.com",
    imap_port: int = 993,
    smtp_port: int = 587
) -> str:
    """Sets up your email account credentials. Use App Passwords for Gmail."""
    config_data = {
        "EMAIL_USER": email_user,
        "EMAIL_PASS": email_pass,
        "IMAP_SERVER": imap_server,
        "SMTP_SERVER": smtp_server,
        "IMAP_PORT": str(imap_port),
        "SMTP_PORT": str(smtp_port)
    }
    config_manager.save_config(config_data)
    return f"Setup successful for {email_user}. You can now list and draft emails."

@mcp.tool()
def list_unread_emails() -> List[dict]:
    """Lists unread emails without marking them as read in your inbox."""
    print("DEBUG: Executing tool list_unread_emails")
    if not oauth_manager.is_authenticated() and not config_manager.is_configured():
        return [{"error": "Not authenticated. Use 'get_authorization_url' to sign in with Google."}]
    
    emails = email_service.get_unread_emails()
    if not emails:
        return [{"message": "No unread emails found."}]
    return [e.model_dump() for e in emails]

@mcp.tool()
def search_emails(query: str) -> List[dict]:
    """Searches for emails across your inbox using a keyword (Subject or Content)."""
    print(f"DEBUG: Executing tool search_emails with query: {query}")
    if not oauth_manager.is_authenticated() and not config_manager.is_configured():
        return [{"error": "Not authenticated. Use 'get_authorization_url' to sign in with Google."}]
    
    emails = email_service.search_emails(query)
    if not emails:
        return [{"message": f"No emails found matching '{query}'."}]
    return [e.model_dump() for e in emails]

@mcp.tool()
def draft_reply(email_id: str) -> str:
    """Generates a personal draft reply for a specific email."""
    if not oauth_manager.is_authenticated() and not config_manager.is_configured():
        return "Error: Not authenticated. Use 'get_authorization_url' to sign in with Google."
        
    email = email_service.get_email_by_id(email_id)
    if not email:
        return f"Error: Email with ID {email_id} not found."
    
    style = memory.load_style()
    
    # AI logic: Combining style profile with email context
    greeting = style.preferred_greetings[0] if style.preferred_greetings else "Hi"
    closing = style.preferred_closings[0] if style.preferred_closings else "Best,"
    
    draft = f"{greeting} {email.sender.split('<')[0].strip() if '<' in email.sender else email.sender.split('@')[0]},\n\n"
    draft += f"Thank you for your email regarding '{email.subject}'.\n\n"
    draft += "I'm looking into your request and will provide a full update soon.\n\n"
    draft += f"{closing}\n"
    
    return draft

@mcp.tool()
def save_draft(to_email: str, subject: str, body: str) -> str:
    """Saves a draft email to your Gmail account for later review."""
    print(f"DEBUG: Executing tool save_draft for {to_email}")
    if not oauth_manager.is_authenticated() and not config_manager.is_configured():
        return "Error: Not authenticated. Use 'get_authorization_url' to sign in with Google."
        
    success = email_service.save_draft_message(to_email, subject, body)
    if success:
        return f"Draft successfully saved to your '[Gmail]/Drafts' folder for {to_email}."
    else:
        return "Failed to save draft. Check your connection and IMAP settings."

@mcp.tool()
def send_email(to_email: str, subject: str, body: str) -> str:
    """Sends a finalized email to a recipient."""
    if not oauth_manager.is_authenticated() and not config_manager.is_configured():
        return "Error: Not authenticated. Use 'get_authorization_url' to sign in with Google."
        
    success = email_service.send_email_message(to_email, subject, body)
    if success:
        return f"Email successfully sent to {to_email}."
    else:
        return "Failed to send email. Check your SMTP configuration and credentials."

@mcp.tool()
def regenerate_reply(email_id: str, feedback: str) -> str:
    """Regenerates a reply draft with specific natural language feedback."""
    email = mock_data.get_email_by_id(email_id)
    if not email:
        return f"Error: Email with ID {email_id} not found."
        
    # Simulate feedback-driven regeneration
    if "shorter" in feedback.lower():
        return f"Hi,\n\nI got your email about {email.subject}. I'm on it.\n\nBest,\nMe"
    
    return f"REGENERATED DRAFT for {email_id} with feedback: {feedback}"

@mcp.tool()
def analyze_user_edits(email_id: str, original_draft: str, final_email: str) -> str:
    """Analyzes differences between AI draft and final sent email to learn style."""
    # Simple heuristic-based learning
    learned_items = []
    
    # Check for new greetings
    first_line = final_email.split('\n')[0]
    if "Hi" not in first_line and "Hello" not in first_line:
        memory.update_style_profile("greeting", first_line.split(',')[0].strip())
        learned_items.append(f"Learned new greeting: {first_line}")
        
    # Check for new closings
    last_lines = final_email.strip().split('\n')[-2:]
    for line in last_lines:
        if line.strip() in ["Best,", "Regards,", "Thanks,"]:
            continue
        if "," in line:
            memory.update_style_profile("closing", line.strip())
            learned_items.append(f"Learned new closing: {line}")
            break
            
    if learned_items:
        return f"Analysis complete. Learned: {', '.join(learned_items)}"
    return "Analysis complete. No significant style changes detected."

if __name__ == "__main__":
    # import os
    # transport = os.getenv("MCP_TRANSPORT", "stdio")
    # port = int(os.getenv("PORT", "8000"))
    
    # if transport == "sse":
    #     print(f"Starting SSE server on port {port}...")
    #     # FORCE bind to 0.0.0.0 for AWS App Runner
    #     # FastMCP's run() method might not be passing kwargs to uvicorn correctly in all versions.
    #     # Accessing the underlying settings/config is safer.
    #     try:
    #         mcp.settings.host = "0.0.0.0"
    #         mcp.settings.port = port
    #     except AttributeError:
    #         pass # Fallback
            
    #     # Try running with explicit host kwarg again, just in case
    #     try:
    #         mcp.run(transport="sse", port=port, host="0.0.0.0")
    #     except TypeError:
    #          mcp.run(transport="sse", port=port)
    # else:
    #     mcp.run(transport="stdio")

    mcp.run(transport="http",host="0.0.0.0", port=8001)
