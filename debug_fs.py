import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "mcp-client"))
from client import MCPMultiClient

async def test_call():
    async with MCPMultiClient() as client:
        await client.connect("filesystem")
        
        args = {"path": "/Users/sachinmishra/Desktop/Data Analytics ICT/porfolio.py"}
        res = await client.call_tool("filesystem", "read_file", args)
        print("Result:", repr(res.result))
        print("is_error:", res.is_error)
        print("error_message:", repr(res.error_message))
        
        args = {"path": "/Users/sachinmishra/Desktop/Data Analytics ICT/Notebooks"}
        res2 = await client.call_tool("filesystem", "list_directory", args)
        print("Result:", repr(res2.result))
        print("is_error:", res2.is_error)
        print("error_message:", repr(res2.error_message))

if __name__ == "__main__":
    asyncio.run(test_call())
