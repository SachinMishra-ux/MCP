import os
import sys

# Ensure the backend directory is in the Python path
# This allows imports like 'from database import ...' inside main.py to work
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from fastmcp import FastMCP
from main import app  # Import the FastAPI app from backend/main.py

from auth import set_mcp_token

# Convert FastAPI app to MCP server
mcp = FastMCP.from_fastapi(
    app=app,
    name="Health Monitor server",
)

@mcp.tool()
async def login(username: str, password: str) -> str:
    """
    Login to the health monitor system.
    This tool stores the session token internally so other tools work automatically.
    """
    # Simply call the internal app's login logic
    # The set_mcp_token call is now handled automatically inside auth.py
    from schemas import UserLogin
    from database import get_session
    from auth import login_json
    
    async for session in get_session():
        try:
            result = await login_json(
                user_in=UserLogin(username=username, password=password),
                session=session
            )
            return f"Successfully logged in as {username}. Session token saved."
        except Exception as e:
            return f"Login failed: {str(e)}"

# --- Resources ---
@mcp.resource("health://docs/vitals-ranges")
def get_vitals_ranges() -> str:
    """Provides standard healthy ranges for various vital signs."""
    return """
Healthy Vital Sign Ranges:
- Heart Rate: 60 - 100 bpm (at rest)
- SpO2 (Oxygen Saturation): 95% - 100%
- Blood Glucose: 70 - 130 mg/dL (before meals)
- Blood Pressure: Less than 120/80 mmHg
- Temperature: 97.8°F - 99.1°F (36.5°C - 37.3°C)
    """

# --- Prompts ---
@mcp.prompt("analyze-health")
def analyze_health_prompt(username: str) -> str:
    """Creates a prompt template for analyzing a user's health data."""
    return f"""
Please analyze the recent vital signs for user '{username}'.
1. Use the 'get_my_vitals' tool to fetch the latest data.
2. Compare the values against the standard ranges found in the 'health://docs/vitals-ranges' resource.
3. Provide a concise summary of the health status.
4. If any values are out of range, suggest that the user consults a medical professional.
    """

if __name__ == "__main__":
    mcp.run()
