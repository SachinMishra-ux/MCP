import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "mcp-client"))
from app import get_client_proxy

def test_proxy():
    proxy = get_client_proxy()
    print("Connecting filesystem...")
    success, msg = proxy.connect("filesystem")
    print(success, msg)
    
    tools = proxy.get_all_tools()
    print(f"Tools available: {[t['tool'].name for t in tools]}")
    
    res = proxy.call_tool("filesystem", "list_directory", {"path": "/Users/sachinmishra/Desktop/Data Analytics ICT"})
    print("Result:", res.result)
    print("Disconnecting...")
    proxy.disconnect("filesystem")
    print("Done.")

if __name__ == "__main__":
    test_proxy()
