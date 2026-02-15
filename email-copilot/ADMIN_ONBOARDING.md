# Admin Onboarding: Setup Google OAuth2

Follow these steps to configure your Email Copilot application. This is a one-time setup that enables end-users to "Sign in with Google."

## Step 1: Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project dropdown and select **New Project**.
3. Name it "Email Copilot" and click **Create**.

## Step 2: Enable Gmail API
1. In the sidebar, go to **APIs & Services > Library**.
2. Search for **"Gmail API"**.
3. Click it and then click **Enable**.

## Step 3: Configure OAuth Consent Screen
1. Go to **APIs & Services > OAuth consent screen**.
2. Select **External** and click **Create**.
3. Fill in the required app information (App name, User support email, Developer contact info).
4. In the **Scopes** section, add: `https://mail.google.com/`.
5. In the **Test users** section, add the email addresses of the users who will use the app.

## Step 4: Create OAuth 2.0 Credentials
1. Go to **APIs & Services > Credentials**.
2. Click **Create Credentials > OAuth client ID**.
3. Select **Web application** as the Application type.
4. Add `http://localhost` (or your deployment URL) to **Authorized redirect URIs**.
5. Click **Create**. You will see your **Client ID** and **Client Secret**.

## Step 5: Configure the MCP Server
You have two ways to apply these keys:

### Option A: Automation (Recommended)
Set these environment variables in your deployment environment (or `.env` file):
```bash
GOOGLE_CLIENT_ID="your-client-id"
GOOGLE_CLIENT_SECRET="your-client-secret"
```
The server will automatically detect these at startup.

### Option B: Using the MCP Tool
Run the following tool command via Claude:
> "Configure my Email Copilot app with Client ID: [ID] and Client Secret: [SECRET]"
