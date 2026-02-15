# Personal Email Copilot MCP Server

A specialized MCP server that helps you manage emails and drafts replies while learning your unique writing style.

## Features
- **Unread List**: Quickly see what's pending in your inbox.
- **Smart Drafting**: Automatically generates replies based on thread context and your style profile.
- **Style Learning**: Analyzes your manual edits to drafts to refine its mimicry of your tone and formality.
- **Simulated Backend**: Works out-of-the-box with mock data for safe testing.

## Tools
- `list_unread_emails`: Returns structured metadata for unread messages.
- `draft_reply`: Generates a context-aware reply using personal style pointers.
- `regenerate_reply`: Refines drafts with natural language instructions.
- `analyze_user_edits`: Compares AI drafts with final versions to learn your style.

## Standard Authentication (OAuth2)
The Email Copilot follows a professional two-tier authentication flow:

### 1. Application Setup (Admin Action)
Before any user can sign in, the application must be registered with Google.
1.  **Get Credentials**: Obtain a Client ID and Client Secret from the [Google Cloud Console](https://console.cloud.google.com/).
2.  **Configure App**: Run the `configure_mcp_app` tool:
    > "Configure my Email Copilot app with Client ID: [ID] and Client Secret: [SECRET]"
3.  **Result**: The configuration is stored once for the entire deployment.

### 2. User Sign-In (End-User Action)
Once configured, users can connect their personal accounts seamlessly:
1.  **Get Link**: Ask Claude, "Get my authorization URL."
2.  **Sign In**: Click the Google link in your browser and authorize the app.
3.  **Complete**: Copy the code from Google and tell Claude, "Authorize with code: [YOUR_CODE]".

### 3. Benefits
- **No App Passwords**: More secure and follows standard protocols.
- **Automatic Refresh**: Your session stays active without re-authenticating.

### 3. Verification
Your credentials are encrypted and stored in `~/.email-copilot/config.json`, making the application itself completely portable and generic.

## Deployment with Docker
If you deploy this to the cloud, ensure you mount a volume to `/root/.email-copilot` to persist your configuration.

```bash
docker build -t email-copilot .
docker run -v ~/.email-copilot:/root/.email-copilot email-copilot
```

## Available Tools
- `get_setup_status`: Returns whether your account is ready.
- `setup_email_account`: Configure your credentials dynamically.
- `list_unread_emails`: Fetches messages from your real inbox.
- `draft_reply`: Generates a context-aware reply draft.
- `send_email`: Sends an email through your SMTP server.
- `analyze_user_edits`: Learns your writing style.
