# Filesystem MCP Server

A simple local MCP server that allows you to list directories and read files from your system.

## Setup

1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Running Locally (Stdio)
You can run the server directly (it listens on Stdio):
```bash
python server.py
```

### Inspecting
If you have the MCP Inspector installed:
```bash
npx @modelcontextprotocol/inspector python server.py
```

### Adding to Claude Desktop
Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "python3",
      "args": [
        "/Users/sachinmishra/Desktop/MCP/filesystem-server/server.py"
      ]
    }
  }
}
```
*Note: Make sure to use the absolute path to `server.py`.*
