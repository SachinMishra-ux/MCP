import os
import sys

# Add backend to path so we can import the FastAPI app
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from fastmcp import FastMCP
from main import app  # Import the FastAPI app from backend

# Convert all FastAPI endpoints into MCP tools automatically
mcp = FastMCP.from_fastapi(
    app=app,
    name="Health Monitor MCP Server",
)

if __name__ == "__main__":
    mcp.run()
