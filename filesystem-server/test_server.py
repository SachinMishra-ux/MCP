import subprocess
import json
import sys
import os

def read_json_message(process):
    """Read a JSON-RPC message from stdout."""
    while True:
        line = process.stdout.readline()
        if not line:
            return None
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            # Skip debug output or non-JSON lines
            continue

def test_server():
    server_path = os.path.abspath("server.py")
    
    # Start the server process
    process = subprocess.Popen(
        [sys.executable, server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True,
        bufsize=1
    )

    try:
        # 1. Send Initialize Request
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "id": 0,
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0"}
            }
        }
        print(f"Sending Initialize...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()

        # 2. Read Initialize Response
        response = read_json_message(process)
        if response and response.get("id") == 0:
            print("Initialize Response Received.")
            # print(json.dumps(response, indent=2))
        else:
            print("Failed to receive initialize response.")
            return

        # 3. Send Initialized Notification
        initialized_note = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        print("Sending Initialized Notification...")
        process.stdin.write(json.dumps(initialized_note) + "\n")
        process.stdin.flush()

        # 4. Request Tools List
        tools_request = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        }
        print(f"Sending Tools List Request...")
        process.stdin.write(json.dumps(tools_request) + "\n")
        process.stdin.flush()

        # 5. Read Tools Response
        response = read_json_message(process)
        if response and response.get("id") == 1:
            print("\nSuccessfully Connected! Available Tools:")
            tools = response.get("result", {}).get("tools", [])
            for tool in tools:
                print(f"- {tool['name']}: {tool.get('description', 'No description')}")
        else:
            print("Failed to get tools list.")
            if response:
                print(json.dumps(response, indent=2))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        process.terminate()

if __name__ == "__main__":
    test_server()
