from fastmcp import FastMCP
import httpx
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# This MCP server acts as a client to the FastAPI backend
API_URL = os.getenv("API_URL", "http://localhost:8000")

mcp = FastMCP("Health Monitor")

# Store token (in production, use proper credential management)
_token = None

@mcp.tool()
async def login(username: str, password: str) -> str:
    """
    Login to the health monitoring system and obtain an access token.
    
    Args:
        username: User's username
        password: User's password
    
    Returns:
        Success message with token info
    """
    global _token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/auth/token",
            data={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            _token = data["access_token"]
            return f"Login successful! Token obtained."
        else:
            return f"Login failed: {response.json().get('detail', 'Unknown error')}"

@mcp.tool()
async def register_user(username: str, password: str) -> str:
    """
    Register a new user in the health monitoring system.
    
    Args:
        username: Desired username
        password: Desired password
    
    Returns:
        Success message
    """
    global _token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/auth/register",
            json={"username": username, "password": password}
        )
        if response.status_code == 200:
            data = response.json()
            _token = data["access_token"]
            return f"Registration successful! User '{username}' created and logged in."
        else:
            return f"Registration failed: {response.json().get('detail', 'Unknown error')}"

@mcp.tool()
async def get_latest_vitals() -> str:
    """
    Get the latest vital signs for the authenticated user.
    
    Returns:
        JSON string with latest vitals (heart rate, glucose, SpO2, etc.)
    """
    if not _token:
        return "Error: Not authenticated. Please login first."
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_URL}/vitals",
            headers={"Authorization": f"Bearer {_token}"}
        )
        if response.status_code == 200:
            vitals = response.json()
            if not vitals:
                return "No vitals recorded yet."
            
            # Format nicely
            result = "Latest Vitals:\n"
            for vital in vitals[:5]:  # Show last 5
                result += f"- {vital['metric']}: {vital['value']} (at {vital['timestamp']})\n"
            return result
        else:
            return f"Error fetching vitals: {response.json().get('detail', 'Unknown error')}"

@mcp.tool()
async def submit_vital(metric: str, value: float) -> str:
    """
    Submit a new vital sign reading for the authenticated user.
    
    Args:
        metric: Type of vital (e.g., 'heart_rate', 'glucose', 'spo2', 'blood_pressure')
        value: The measured value
    
    Returns:
        Confirmation message
    """
    if not _token:
        return "Error: Not authenticated. Please login first."
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/vitals",
            json={"metric": metric, "value": value},
            headers={"Authorization": f"Bearer {_token}"}
        )
        if response.status_code == 200:
            data = response.json()
            return f"Vital recorded: {metric} = {value} (ID: {data['id']})"
        else:
            return f"Error submitting vital: {response.json().get('detail', 'Unknown error')}"

@mcp.tool()
async def get_vital_trend(metric: str, limit: int = 10) -> str:
    """
    Get trend data for a specific vital sign metric.
    
    Args:
        metric: The vital metric to analyze (e.g., 'heart_rate', 'glucose')
        limit: Number of recent readings to include (default 10)
    
    Returns:
        Formatted trend data with statistics
    """
    if not _token:
        return "Error: Not authenticated. Please login first."
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_URL}/vitals",
            headers={"Authorization": f"Bearer {_token}"}
        )
        if response.status_code == 200:
            vitals = response.json()
            
            # Filter by metric
            filtered = [v for v in vitals if v['metric'] == metric][:limit]
            
            if not filtered:
                return f"No data found for metric: {metric}"
            
            values = [v['value'] for v in filtered]
            avg = sum(values) / len(values)
            min_val = min(values)
            max_val = max(values)
            
            result = f"Trend for {metric} (last {len(filtered)} readings):\n"
            result += f"Average: {avg:.2f}\n"
            result += f"Min: {min_val:.2f}\n"
            result += f"Max: {max_val:.2f}\n"
            result += f"\nRecent values: {', '.join(str(v) for v in values[:5])}"
            
            return result
        else:
            return f"Error fetching trend: {response.json().get('detail', 'Unknown error')}"

if __name__ == "__main__":
    mcp.run()
