import re

with open("mcp-client/app.py", "r") as f:
    content = f.read()

# 1. Add theme to session state
content = content.replace(
    'if "pending_disconnect" not in st.session_state:\n    st.session_state.pending_disconnect = None',
    'if "pending_disconnect" not in st.session_state:\n    st.session_state.pending_disconnect = None\nif "theme" not in st.session_state:\n    st.session_state.theme = "Dark"'
)

# 2. Add Theme toggle to sidebar
sidebar_search = '''    # ── LLM Settings ─────────────────────────────────────────'''
sidebar_replace = '''    # ── Theme Settings ─────────────────────────────────────────
    st.caption("🎨 THEME")
    theme_choice = st.radio(
        "Theme", ["Dark", "Light"], 
        index=0 if st.session_state.theme == "Dark" else 1,
        horizontal=True, 
        label_visibility="collapsed"
    )
    if theme_choice != st.session_state.theme:
        st.session_state.theme = theme_choice
        st.rerun()

    st.divider()

    # ── LLM Settings ─────────────────────────────────────────'''
content = content.replace(sidebar_search, sidebar_replace)

# 3. Dynamic CSS
css_search = r'st\.markdown\("""\n<style>\n(?:.*?)<\/style>\n""", unsafe_allow_html=True\)'
# We will just put a placeholder for dynamic CSS
dynamic_css = '''
# ─────────────────────────────────────────────────────────────
# Custom CSS (Dynamic via Session State)
# ─────────────────────────────────────────────────────────────
def get_css(theme):
    if theme == "Light":
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
            .stApp { background: #f8fafc; color: #0f172a; }
            [data-testid="stSidebar"] { background: #ffffff !important; border-right: 1px solid #e2e8f0; }
            .mcp-header { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 16px; padding: 20px 28px; margin-bottom: 24px; display: flex; align-items: center; gap: 14px; }
            .mcp-header h1 { margin: 0; font-size: 1.8rem; font-weight: 700; background: linear-gradient(90deg, #4f46e5, #9333ea); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .mcp-header p { margin: 2px 0 0; color: #475569; font-size: 0.9rem; }
            .server-card { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; transition: border-color 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
            .server-card:hover { border-color: #6366f1; }
            .server-card.connected { border-color: #10b981; background: #ecfdf5; }
            .status-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
            .dot-green { background: #10b981; box-shadow: 0 0 6px rgba(16,185,129,0.5); }
            .dot-red { background: #ef4444; }
            .dot-yellow { background: #f59e0b; box-shadow: 0 0 6px rgba(245,158,11,0.5); }
            .chat-user { background: #e0e7ff; border: 1px solid #c7d2fe; border-radius: 16px 16px 4px 16px; padding: 14px 18px; margin: 6px 0 6px 10%; color: #1e1b4b; }
            .chat-assistant { background: #f1f5f9; border: 1px solid #e2e8f0; border-radius: 16px 16px 16px 4px; padding: 14px 18px; margin: 6px 10% 6px 0; color: #334155; line-height: 1.65; }
            .chat-label { font-size: 0.72rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 6px; }
            .label-user { color: #4f46e5; }
            .label-assistant { color: #059669; }
            .tool-call-block { background: #ffffff; border-left: 3px solid #6366f1; border-radius: 0 8px 8px 0; padding: 10px 14px; margin: 8px 0; font-size: 0.85rem; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
            .tool-result-block { background: #ecfdf5; border-left: 3px solid #10b981; border-radius: 0 8px 8px 0; padding: 10px 14px; margin: 4px 0 10px; font-size: 0.83rem; color: #064e3b; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
            .tool-error-block { background: #fef2f2; border-left: 3px solid #ef4444; border-radius: 0 8px 8px 0; padding: 10px 14px; margin: 4px 0 10px; font-size: 0.83rem; color: #7f1d1d; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
            .stTextInput > div > div > input, .stTextArea > div > div > textarea { background: #ffffff !important; border: 1px solid #cbd5e1 !important; border-radius: 10px !important; color: #0f172a !important; }
            .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus { border-color: #6366f1 !important; box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important; }
            .stButton > button { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 500 !important; transition: opacity 0.2s; }
            .stButton > button:hover { opacity: 0.88 !important; }
            .tool-pill { display: inline-block; background: #e0e7ff; border: 1px solid #c7d2fe; border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; color: #4338ca; margin: 2px; }
            .section-title { color: #64748b; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; margin: 16px 0 8px; }
            hr { border-color: #e2e8f0 !important; }
            [data-testid="stExpander"] { background: #f8fafc !important; border: 1px solid #e2e8f0 !important; border-radius: 8px !important; }
            [data-testid="stSelectbox"] div[data-baseweb] { background: #ffffff !important; border-color: #cbd5e1 !important; color: #0f172a !important; }
            #MainMenu, footer { visibility: hidden; }
            .block-container { padding-top: 1.5rem; }
        </style>
        """
    else:
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
            html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
            .stApp { background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%); color: #e2e8f0; }
            [data-testid="stSidebar"] { background: rgba(15, 15, 30, 0.95) !important; border-right: 1px solid rgba(99, 102, 241, 0.2); }
            .mcp-header { background: linear-gradient(90deg, rgba(99,102,241,0.15) 0%, rgba(139,92,246,0.1) 100%); border: 1px solid rgba(99,102,241,0.3); border-radius: 16px; padding: 20px 28px; margin-bottom: 24px; display: flex; align-items: center; gap: 14px; }
            .mcp-header h1 { margin: 0; font-size: 1.8rem; font-weight: 700; background: linear-gradient(90deg, #818cf8, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .mcp-header p { margin: 2px 0 0; color: #94a3b8; font-size: 0.9rem; }
            .server-card { background: rgba(30, 30, 60, 0.6); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 12px; padding: 12px 16px; margin-bottom: 10px; transition: border-color 0.2s; }
            .server-card:hover { border-color: rgba(99, 102, 241, 0.5); }
            .server-card.connected { border-color: rgba(52, 211, 153, 0.4); background: rgba(20, 50, 40, 0.5); }
            .status-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
            .dot-green { background: #34d399; box-shadow: 0 0 6px #34d399; }
            .dot-red { background: #f87171; }
            .dot-yellow { background: #fbbf24; box-shadow: 0 0 6px #fbbf24; }
            .chat-user { background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(139,92,246,0.2)); border: 1px solid rgba(99,102,241,0.3); border-radius: 16px 16px 4px 16px; padding: 14px 18px; margin: 6px 0 6px 10%; color: #e2e8f0; }
            .chat-assistant { background: rgba(30, 30, 60, 0.7); border: 1px solid rgba(99,102,241,0.15); border-radius: 16px 16px 16px 4px; padding: 14px 18px; margin: 6px 10% 6px 0; color: #cbd5e1; line-height: 1.65; }
            .chat-label { font-size: 0.72rem; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 6px; }
            .label-user { color: #818cf8; }
            .label-assistant { color: #34d399; }
            .tool-call-block { background: rgba(15, 15, 30, 0.8); border-left: 3px solid #818cf8; border-radius: 0 8px 8px 0; padding: 10px 14px; margin: 8px 0; font-size: 0.85rem; }
            .tool-result-block { background: rgba(15, 30, 25, 0.8); border-left: 3px solid #34d399; border-radius: 0 8px 8px 0; padding: 10px 14px; margin: 4px 0 10px; font-size: 0.83rem; color: #a7f3d0; }
            .tool-error-block { background: rgba(30, 15, 15, 0.8); border-left: 3px solid #f87171; border-radius: 0 8px 8px 0; padding: 10px 14px; margin: 4px 0 10px; font-size: 0.83rem; color: #fca5a5; }
            .stTextInput > div > div > input, .stTextArea > div > div > textarea { background: rgba(20, 20, 40, 0.9) !important; border: 1px solid rgba(99,102,241,0.3) !important; border-radius: 10px !important; color: #e2e8f0 !important; }
            .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus { border-color: rgba(99,102,241,0.7) !important; box-shadow: 0 0 0 2px rgba(99,102,241,0.15) !important; }
            .stButton > button { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; color: white !important; border: none !important; border-radius: 8px !important; font-weight: 500 !important; transition: opacity 0.2s; }
            .stButton > button:hover { opacity: 0.88 !important; }
            .tool-pill { display: inline-block; background: rgba(99,102,241,0.2); border: 1px solid rgba(99,102,241,0.3); border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; color: #a5b4fc; margin: 2px; }
            .section-title { color: #94a3b8; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; margin: 16px 0 8px; }
            hr { border-color: rgba(99,102,241,0.15) !important; }
            [data-testid="stExpander"] { background: rgba(20,20,40,0.5) !important; border: 1px solid rgba(99,102,241,0.15) !important; border-radius: 8px !important; }
            [data-testid="stSelectbox"] div[data-baseweb] { background: rgba(20,20,40,0.9) !important; border-color: rgba(99,102,241,0.3) !important; color: #e2e8f0 !important; }
            #MainMenu, footer { visibility: hidden; }
            .block-container { padding-top: 1.5rem; }
        </style>
        """

st.markdown(get_css(st.session_state.get("theme", "Dark")), unsafe_allow_html=True)
'''
content = re.sub(css_search, dynamic_css, content, flags=re.DOTALL)

with open("mcp-client/app.py", "w") as f:
    f.write(content)

print("Patching complete.")
