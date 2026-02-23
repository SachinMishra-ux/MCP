import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "mcp-client"))
from client import MCPMultiClient

async def test_connections():
    async with MCPMultiClient() as client:
        # Test filesystem
        print("Testing filesystem...")
        success, msg = await client.connect("filesystem")
        print(f"filesystem: {success} - {msg}")
        
        # Test health-monitor
        print("Testing health-monitor...")
        success, msg = await client.connect("health-monitor")
        print(f"health-monitor: {success} - {msg}")
        
        # For email-copilot-local, we'd need it running. 
        # But we can just test if the stdio process ones work first.
        
if __name__ == "__main__":
    asyncio.run(test_connections())
