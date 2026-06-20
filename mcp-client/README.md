# MCP Hub — Custom Python MCP Client + Streamlit UI

A custom multi-server MCP client that aggregates all your MCP servers into a single Streamlit chat interface.

## Features

- 🔗 Connect to **multiple MCP servers** simultaneously (stdio + HTTP/remote)
- 🤖 **AI-powered chat** using Anthropic Claude, OpenAI GPT, or Groq
- 🔧 **Tool discovery** — automatically lists all tools from connected servers
- 🌐 **Remote server support** — add any HTTP MCP server via URL
- 💬 **Expandable tool calls** — see exactly what tools were called and the results
- ➕ **Dynamic server management** — add new remote servers from the UI

## Servers Integrated

| Server | Transport | Description |
|---|---|---|
| `filesystem` | stdio | Browse local files and directories |
| `email-copilot-local` | HTTP | Email Copilot (local port 8001) |
| `health-monitor` | stdio | Health vitals monitor |

## Setup

### 1. Install dependencies

```bash
cd mcp-client
pip install -r requirements.txt
```

Or using uv (from project root):
```bash
uv add streamlit anthropic openai pyyaml
```

### 2. Configure API Key

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY, OPENAI_API_KEY, or GROQ_API_KEY
```

### 3. (Optional) Start the Email Copilot HTTP server first

```bash
# In a separate terminal:
cd email-copilot
python server.py
# → Listens on http://localhost:8001/mcp
```

### 4. Run the Streamlit app

```bash
cd mcp-client
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## Adding a Remote Server

**Option A — Edit `config.yaml`** (permanent):
```yaml
my-remote-server:
  type: http
  url: "https://my-server.example.com/mcp"
  description: "My remote MCP server"
  enabled: true
```

**Option B — Use the UI** (also saves to config.yaml):
In the sidebar → "Add Remote Server" expander → enter name + URL → click Add.

## File Structure

```
mcp-client/
├── app.py           # Streamlit chat UI
├── client.py        # Core MCP multi-server client
├── llm_agent.py     # Anthropic / OpenAI agent wrapper
├── config.yaml      # Server registry
├── requirements.txt
├── .env.example
└── README.md
```

## Architecture

```
Streamlit UI (app.py)
    │
    ├── MCPMultiClient (client.py)
    │       ├── filesystem   ←→ stdio subprocess
    │       ├── email-copilot ←→ HTTP (localhost:8001)
    │       └── health-monitor ←→ stdio subprocess
    │
    └── LLM Agent (llm_agent.py)
            ├── AnthropicAgent  (Claude)
            └── OpenAIAgent     (GPT / Groq)
```
---

```

           ┌──────────────────────────────────────────┐
           │          Streamlit UI (app.py)           │
           └────────────────────┬─────────────────────┘
                                │ Calls proxy methods
           ┌────────────────────▼─────────────────────┐
           │      Background Worker & Async Loop      │
           └────────────────────┬─────────────────────┘
                                │ Orchestrates
     ┌──────────────────────────┴──────────────────────────┐
     ▼                                                     ▼
┌──────────────────────────┐                         ┌───────────┐
│  Multi-Server Manager    │                         │ LLM Agent │
│       (client.py)        │                         │  (llm_...)│
└────────────┬─────────────┘                         └─────┬─────┘
  Reads/Writes config.yaml                                 │ Drives
             │                                             │
             ▼                                             ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ Local Stdio Servers (Filesystem, Email-copilot, Health)     │
  │ Remote HTTP Servers (Salary Prediction API)                 │
  └─────────────────────────────────────────────────────────────┘
```