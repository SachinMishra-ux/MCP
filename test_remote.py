import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "mcp-client"))
from app import get_client_proxy

def test_proxy():
    proxy = get_client_proxy()
    server_name = "Salary prediction Server"
    print(f"Connecting {server_name}...")
    success, msg = proxy.connect(server_name)
    print("Success:", success)
    print("Message:", msg)
    
    if success:
        tools = proxy.get_all_tools()
        print(f"Tools available: {[t['tool'].name for t in tools]}")
        print("Disconnecting...")
        proxy.disconnect(server_name)
    print("Done.")

if __name__ == "__main__":
    test_proxy()
