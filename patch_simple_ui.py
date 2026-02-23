import re

with open("mcp-client/app.py", "r") as f:
    content = f.read()

# Remove the Theme radio button
theme_search = r'''    # ── Theme Settings ─────────────────────────────────────────
    st\.caption\("🎨 THEME"\)
    theme_choice = st\.radio\(
        "Theme", \["Dark", "Light"\], 
        index=0 if st\.session_state\.theme == "Dark" else 1,
        horizontal=True, 
        label_visibility="collapsed"
    \)
    if theme_choice != st\.session_state\.theme:
        st\.session_state\.theme = theme_choice
        st\.rerun\(\)

    st\.divider\(\)'''
content = re.sub(theme_search, '', content)

# Remove the dynamic CSS function and the markdown call
css_search = r'''# ─────────────────────────────────────────────────────────────
# Custom CSS \(Dynamic via Session State\)
# ─────────────────────────────────────────────────────────────
def get_css\(theme\):.*?st\.markdown\(get_css\(st\.session_state\.get\("theme", "Dark"\)\), unsafe_allow_html=True\)'''
content = re.sub(css_search, '', content, flags=re.DOTALL)

# Strip out the HTML divs from chat blocks and use standard st.chat_message
user_chat_search = r'''            st\.markdown\(f"""
            <div class="chat-user">
                <div class="chat-label label-user">You</div>
                \{msg\["content"\]\}
            </div>
            """, unsafe_allow_html=True\)'''

assistant_chat_search = r'''            st\.markdown\(f"""
            <div class="chat-assistant">
                <div class="chat-label label-assistant">MCP Agent</div>
                \{msg\["content"\]\}
            </div>
            """, unsafe_allow_html=True\)'''

content = content.replace(user_chat_search, '            with st.chat_message("user"):\n                st.write(msg["content"])')
content = content.replace(assistant_chat_search, '            with st.chat_message("assistant"):\n                st.write(msg["content"])')

# Simplify tool result blocks
tool_search = r'''                        st\.markdown\(
                            f"<div class='\{'tool-result-block' if not tc\.get\('is_error'\) else 'tool-error-block'\}'>"
                            f"<pre style='color:\{color\}; margin:0; white-space:pre-wrap'>\{tc\['result'\]\}</pre>"
                            f"</div>",
                            unsafe_allow_html=True,
                        \)'''
content = re.sub(tool_search, '                        st.code(tc["result"], language="json" if not tc.get("is_error") else "text")', content)

# Remove mcp-header
header_search = r'''st\.markdown\(f"""
<div class="mcp-header">
    <div style="font-size:2.5rem; line-height:1;">🔗</div>
    <div>
        <h1>MCP Hub</h1>
        <p>
            <span style="color:#34d399">●</span> \{connected_count\} server\(s\) connected &nbsp;·&nbsp;
            <span style="color:#818cf8">🔧</span> \{tool_count\} tool\(s\) available
        </p>
    </div>
</div>
""", unsafe_allow_html=True\)'''
content = re.sub(header_search, 'st.title("🔗 MCP Hub")\nst.caption(f"● {connected_count} server(s) connected · 🔧 {tool_count} tool(s) available")', content)

zero_server_search = r'''    st\.markdown\("""
    <div style="text-align:center; padding: 60px 20px;">
        <div style="font-size:3rem; margin-bottom:12px;">🔌</div>
        <div style="font-size:1.15rem; color:#94a3b8; font-weight:500;">No servers connected yet</div>
        <div style="color:#64748b; margin-top:8px; font-size:0.9rem;">
            Use the <strong>sidebar</strong> to connect to your MCP servers,<br>
            then start chatting here\.
        </div>
    </div>
    """, unsafe_allow_html=True\)'''
content = re.sub(zero_server_search, '    st.info("🔌 No servers connected yet. Use the sidebar to connect.")', content)

# Remove sidebar custom html header
sidebar_header_search = r'''    st\.markdown\("""
    <div style="text-align:center; padding: 8px 0 16px;">
        <span style="font-size:2.2rem;">🔗</span>
        <div style="font-size:1.1rem; font-weight:700; color:#818cf8; margin-top:4px;">MCP Hub</div>
        <div style="font-size:0.75rem; color:#64748b;">Multi-Server MCP Client</div>
    </div>
    """, unsafe_allow_html=True\)'''
content = re.sub(sidebar_header_search, '    st.header("🔗 MCP Hub")', content)

with open("mcp-client/app.py", "w") as f:
    f.write(content)

print("App simplified.")
