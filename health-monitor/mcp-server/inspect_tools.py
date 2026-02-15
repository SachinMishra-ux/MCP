import os
import sys
import json

# Ensure the backend directory is in the Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from fastmcp import FastMCP
from main import app

mcp = FastMCP.from_fastapi(app=app)

tools = mcp.list_tools()
for tool in tools:
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description}")
# print(f"Parameters: {json.dumps(tool.parameters, indent=2)}")
    print(f"Parameters: {tool.parameters}")
    print("-" * 20)
