"""
app.py — Streamlit UI for the Custom MCP Multi-Server Client

Run with:
    streamlit run app.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Path setup ────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from client import MCPMultiClient, add_remote_server, load_server_configs
from llm_agent import get_agent, StreamChunk

# ─────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MCP Hub",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────




# ─────────────────────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────────────────────
if "mcp_client" not in st.session_state:
    st.session_state.mcp_client = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []   # list of {role, content, tool_calls}
if "llm_history" not in st.session_state:
    st.session_state.llm_history = []    # messages in LLM format
if "connected_servers" not in st.session_state:
    st.session_state.connected_servers = set()
if "server_configs" not in st.session_state:
    st.session_state.server_configs = load_server_configs()
if "status_messages" not in st.session_state:
    st.session_state.status_messages = []
if "pending_connect" not in st.session_state:
    st.session_state.pending_connect = None
if "pending_disconnect" not in st.session_state:
    st.session_state.pending_disconnect = None
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"


# ─────────────────────────────────────────────────────────────
# Async helpers (Streamlit runs sync; we use asyncio.run())
# ─────────────────────────────────────────────────────────────

import threading
import concurrent.futures

class MCPBackgroundWorker:
    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self.client = MCPMultiClient()
        self._ready = threading.Event()
        self._req_queue = None

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._ready.wait()

    def _run(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._main_task())

    async def _main_task(self):
        await self.client.__aenter__()
        self._req_queue = asyncio.Queue()
        self._ready.set()
        
        while True:
            future, action, args, kwargs = await self._req_queue.get()
            try:
                if action == "connect":
                    res = await self.client.connect(*args, **kwargs)
                elif action == "disconnect":
                    res = await self.client.disconnect(*args, **kwargs)
                elif action == "call_tool":
                    res = await self.client.call_tool(*args, **kwargs)
                elif action == "get_all_tools":
                    res = self.client.get_all_tools()
                elif action == "get_tools_for_llm":
                    res = self.client.get_tools_for_llm()
                elif action == "list_server_status":
                    res = self.client.list_server_status()
                elif action == "reload_config":
                    res = self.client.reload_config()
                else:
                    res = None
                
                # We need to set the result in the event loop thread
                self._loop.call_soon_threadsafe(future.set_result, res)
            except Exception as e:
                self._loop.call_soon_threadsafe(future.set_exception, e)
            finally:
                self._req_queue.task_done()

    def execute(self, action, *args, **kwargs):
        """Submit a task to the background worker and wait for the result."""
        future = concurrent.futures.Future()
        def _submit():
            self._req_queue.put_nowait((future, action, args, kwargs))
        self._loop.call_soon_threadsafe(_submit)
        return future.result()


@st.cache_resource
def get_worker() -> MCPBackgroundWorker:
    return MCPBackgroundWorker()


def get_client_proxy():
    """A proxy object that forwards methods to the background worker."""
    worker = get_worker()
    class Proxy:
        def connect(self, name): return worker.execute("connect", name)
        def disconnect(self, name): return worker.execute("disconnect", name)
        def call_tool(self, server, tool, args): return worker.execute("call_tool", server, tool, args)
        def get_all_tools(self): return worker.execute("get_all_tools")
        def get_tools_for_llm(self): return worker.execute("get_tools_for_llm")
        def list_server_status(self): return worker.execute("list_server_status")
        def reload_config(self): return worker.execute("reload_config")
    return Proxy()


async def async_call_agent(user_msg: str, provider: str, api_key: str, model: str):
    """Run the LLM agent and collect all chunks synchronously in Streamlit, proxying tools to worker."""
    proxy = get_client_proxy()
    tools = proxy.get_tools_for_llm()

    agent = get_agent(provider, api_key, model)
    chunks = []

    async def tool_executor(server_name, tool_name, args):
        # We need to proxy through to the background thread
        # Because tool_executor handles async we wrap it
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, proxy.call_tool, server_name, tool_name, args)

    async for chunk in agent.run(
        user_message=user_msg,
        tools=tools,
        history=st.session_state.llm_history,
        tool_executor=tool_executor,
    ):
        chunks.append(chunk)

    return chunks

# Wrapper to properly bridge async agent to sync streamlit without interfering with the background worker
def run_agent_sync(user_msg, provider, api_key, model):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(async_call_agent(user_msg, provider, api_key, model))



# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("🔗 MCP Hub")



    # ── LLM Settings ─────────────────────────────────────────
    st.caption("🤖 LLM SETTINGS")

    provider = st.selectbox(
        "Provider",
        ["Anthropic Claude", "OpenAI GPT", "Groq"],
        label_visibility="collapsed",
        key="llm_provider",
    )

    model_options = {
        "Anthropic Claude": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
        ],
        "OpenAI GPT": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
        ],
        "Groq": [
            "openai/gpt-oss-120b",
            "llama3-8b-8192",
            "mixtral-8x7b-32768",
        ],
    }
    model = st.selectbox(
        "Model",
        model_options[provider],
        label_visibility="collapsed",
        key="llm_model",
    )

    if provider == "Anthropic Claude":
        env_key_name = "ANTHROPIC_API_KEY"
    elif provider == "OpenAI GPT":
        env_key_name = "OPENAI_API_KEY"
    else:
        env_key_name = "GROQ_API_KEY"
    default_key = os.getenv(env_key_name, "")
    api_key = st.text_input(
        "API Key",
        value=default_key,
        type="password",
        placeholder=f"Enter {env_key_name}…",
        label_visibility="collapsed",
    )
    if not api_key:
        st.caption(f"⚠️ Set `{env_key_name}` in `.env` or enter above")

    st.divider()

    # ── Server Management ─────────────────────────────────────
    st.caption("🖥️ SERVERS")

    client = get_client_proxy()
    server_statuses = client.list_server_status()

    for srv in server_statuses:
        name = srv["name"]
        is_connected = srv["connected"]
        type_icon = "🌐" if srv["type"] == "http" else "💻"
        status_icon = "🟢" if is_connected else "🔴"
        tool_info = f" · {srv['tool_count']} tools" if is_connected else ""

        st.markdown(
            f"**{status_icon} {name}** {type_icon}{tool_info}",
        )
        st.caption(srv["description"])

        col1, col2 = st.columns(2)
        with col1:
            if not is_connected:
                if st.button("Connect", key=f"connect_{name}", use_container_width=True):
                    with st.spinner(f"Connecting to {name}…"):
                        success, msg = client.connect(name)
                    if success:
                        st.session_state.connected_servers.add(name)
                        st.success(msg)
                    else:
                        st.error(msg)
                    st.rerun()
        with col2:
            if is_connected:
                if st.button("Disconnect", key=f"disconnect_{name}", use_container_width=True):
                    success, msg = client.disconnect(name)
                    if success:
                        st.session_state.connected_servers.discard(name)
                    st.rerun()
        st.markdown("---")

    st.divider()

    # ── Add Remote Server ─────────────────────────────────────
    st.caption("➕ ADD REMOTE SERVER")
    with st.expander("Add HTTP/Remote Server", expanded=False):
        new_name = st.text_input("Server name", placeholder="my-remote-server", key="new_srv_name")
        new_url  = st.text_input("URL",         placeholder="https://my-server.com/mcp", key="new_srv_url")
        new_auth = st.text_input("Auth Token (Optional)", placeholder="Bearer token...", type="password", key="new_srv_auth")
        new_desc = st.text_input("Description", placeholder="Optional description", key="new_srv_desc")
        if st.button("➕ Add Server", use_container_width=True):
            if new_name and new_url:
                add_remote_server(new_name, new_url, new_auth, new_desc)
                client.reload_config()
                st.success(f"Added '{new_name}'! Click Connect to use it.")
                st.rerun()
            else:
                st.warning("Name and URL are required.")

    st.divider()

    # ── Tool Inspector ────────────────────────────────────────
    all_tools = client.get_all_tools()
    if all_tools:
        st.caption(f"🔧 AVAILABLE TOOLS ({len(all_tools)})")
        with st.expander("View all tools", expanded=False):
            grouped: Dict[str, List] = {}
            for entry in all_tools:
                grouped.setdefault(entry["server"], []).append(entry["tool"])
            for srv_name, tools in grouped.items():
                st.markdown(f"**{srv_name}**")
                for t in tools:
                    st.badge(t.name, color="violet")
                    if t.description:
                        st.caption(f"  ↳ {t.description}")

    # Conversation controls
    st.divider()
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.llm_history = []
        st.rerun()


# ─────────────────────────────────────────────────────────────
# Main area
# ─────────────────────────────────────────────────────────────

# Header
connected_count = len([s for s in client.list_server_status() if s["connected"]])
tool_count = len(client.get_all_tools())

st.title("🔗 MCP Hub")
st.caption(f"● {connected_count} server(s) connected · 🔧 {tool_count} tool(s) available")

# ── No servers connected yet ──────────────────────────────────
if connected_count == 0:
    st.info("🔌 No servers connected yet. Use the sidebar to connect.")

# ── Chat history ─────────────────────────────────────────────
chat_container = st.container()
with chat_container:
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-user">
                <div class="chat-label label-user">You</div>
                {msg["content"]}
            </div>
            """, unsafe_allow_html=True)

        elif msg["role"] == "assistant":
            st.markdown(f"""
            <div class="chat-assistant">
                <div class="chat-label label-assistant">MCP Agent</div>
                {msg["content"]}
            </div>
            """, unsafe_allow_html=True)

            # Show tool calls
            for tc in msg.get("tool_calls", []):
                with st.expander(f"🔧 Tool call: `{tc['tool']}`", expanded=False):
                    st.markdown("**Input:**")
                    st.code(json.dumps(tc["input"], indent=2), language="json")
                    if "result" in tc:
                        label = "Result" if not tc.get("is_error") else "Error"
                        color = "#a7f3d0" if not tc.get("is_error") else "#fca5a5"
                        st.markdown(f"**{label}:**")
                        st.code(tc["result"], language="json" if not tc.get("is_error") else "text")


# ── Chat input ────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)

with st.form(key="chat_form", clear_on_submit=True):
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_input = st.text_input(
            "Message",
            placeholder="Ask anything… e.g. 'List files in /tmp' or 'Check my email auth status'",
            label_visibility="collapsed",
            key="user_input_field",
        )
    with col_btn:
        submitted = st.form_submit_button("Send ➤", use_container_width=True)

# ── Process message ───────────────────────────────────────────
if submitted and user_input.strip():
    if not api_key:
        st.error(f"Please enter your API key in the sidebar (or set `{env_key_name}` in `.env`).")
    elif connected_count == 0:
        st.warning("Please connect at least one server from the sidebar first.")
    else:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input.strip(),
        })
        st.session_state.llm_history.append({
            "role": "user",
            "content": user_input.strip(),
        })

        with st.spinner("🤔 Agent is thinking…"):
            try:
                chunks = run_agent_sync(
                    user_msg=user_input.strip(),
                    provider=provider,
                    api_key=api_key,
                    model=model,
                )

                # Aggregate chunks into one assistant message
                text_parts = []
                tool_calls_display = []
                pending_tool: Optional[Dict] = None

                for chunk in chunks:
                    if chunk.type == "text":
                        text_parts.append(chunk.data)
                    elif chunk.type == "tool_call":
                        # Start a new tool call record
                        pending_tool = {
                            "tool": chunk.data["tool"],
                            "input": chunk.data["input"],
                        }
                    elif chunk.type == "tool_result" and pending_tool:
                        pending_tool["result"] = chunk.data["result"]
                        pending_tool["is_error"] = chunk.data.get("is_error", False)
                        tool_calls_display.append(pending_tool)
                        pending_tool = None

                final_text = "".join(text_parts) or "✅ Done."

                # Save assistant message
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": final_text,
                    "tool_calls": tool_calls_display,
                })

                # Update LLM history (simplified)
                st.session_state.llm_history.append({
                    "role": "assistant",
                    "content": final_text,
                })

            except Exception as e:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": f"❌ **Error:** {str(e)}",
                    "tool_calls": [],
                })

        st.rerun()

# ── Quick action examples ─────────────────────────────────────
if not st.session_state.chat_history and connected_count > 0:
    st.caption("💡 TRY THESE EXAMPLES")
    examples = [
        ("📁", "List files in /tmp"),
        ("📧", "Check my email auth status"),
        ("❤️", "Get my latest health vitals"),
        ("🔍", "Search emails about meeting"),
    ]
    cols = st.columns(len(examples))
    for col, (icon, text) in zip(cols, examples):
        with col:
            if st.button(f"{icon} {text}", use_container_width=True, key=f"ex_{text}"):
                # Inject this as a user message
                st.session_state.chat_history.append({"role": "user", "content": text})
                st.session_state.llm_history.append({"role": "user", "content": text})
                st.rerun()
