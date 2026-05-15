import streamlit as st
import urllib.parse
import datetime
import time
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.utils import ui_log
from src.graph import build_graph


st.set_page_config(page_title="Terminal_Terminal", page_icon="📟", layout="wide")

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False
if "logs" not in st.session_state:
    st.session_state.logs = []
if "graph_app" not in st.session_state:
    st.session_state.graph_app = build_graph()
if "graph_started" not in st.session_state:
    st.session_state.graph_started = False
if "awaiting_resume" not in st.session_state:
    st.session_state.awaiting_resume = False
if "graph_done" not in st.session_state:
    st.session_state.graph_done = False

GRAPH_CONFIG = {"configurable": {"thread_id": "session-1"}, "recursion_limit": 50}

# --- BACKGROUND ANIMATION ---
binary_html = """
<style>
    body { margin: 0; overflow: hidden; background: black; }
    canvas { display: block; }
</style>
<canvas id="binary-canvas"></canvas>
<script>
    const canvas = document.getElementById('binary-canvas');
    const ctx = canvas.getContext('2d');
    let rows, cols, binaryData;
    const fontSize = 18;
    function init() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        cols = Math.ceil(canvas.width / (fontSize * 0.6));
        rows = Math.ceil(canvas.height / fontSize);
        binaryData = Array.from({ length: rows + 1 }, () =>
            Array.from({ length: cols }, () => Math.random() > 0.5 ? "1" : "0").join("")
        );
    }
    let frameCount = 0;
    function draw() {
        frameCount++;
        if (frameCount % 6 !== 0) { requestAnimationFrame(draw); return; }
        ctx.fillStyle = "black";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = "#39FF14";
        ctx.font = fontSize + "px monospace";
        for (let i = 0; i < rows; i++) {
            if (binaryData[i]) {
                binaryData[i] = binaryData[i].substring(1) + (Math.random() > 0.5 ? "1" : "0");
                ctx.fillText(binaryData[i], 0, (i + 1) * fontSize);
            }
        }
        requestAnimationFrame(draw);
    }
    window.addEventListener('resize', init);
    init();
    draw();
</script>
"""
encoded_html = urllib.parse.quote(binary_html)
st.iframe(src=f"data:text/html;charset=utf-8,{encoded_html}", height=1)

# --- THE "NUCLEAR" CSS FIX ---
st.markdown("""
<style>
    /* 1. ANIMATION LAYER */
    iframe {
        position: fixed; top: 0; left: 0; width: 100vw !important; height: 100vh !important;
        z-index: -1; border: none; pointer-events: none; opacity: 0.2;
    }

    /* 2. GLOBAL TRANSPARENCY - TARGETING EVERY POSSIBLE LAYER */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMainViewContainer"],
    [data-testid="stHeader"], [data-testid="stToolbar"], .main, footer,
    [data-testid="stBottom"], [data-testid="stBottomBlockContainer"],
    .stChatInputContainer, div[class*="st-emotion-cache"] {
        background-color: transparent !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* 3. FORCE BODY BLACK (In case of flicker) */
    body { background-color: #000000 !important; }

    /* 4. TERMINAL TEXT */
    .stMarkdown p, h1, h2, h3, label, .stChatMessage p {
        color: #39FF14 !important;
        text-shadow: 0 0 5px rgba(57, 255, 20, 0.8);
        font-family: 'Courier New', monospace !important;
    }

    [data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.9) !important;
        border-right: 1px solid #39FF14;
    }

    .stChatMessage {
        background: rgba(0, 0, 0, 0.8) !important;
        border: 1px solid #39FF14 !important;
        border-radius: 8px !important;
    }

    [data-testid="stChatInput"] {
        background-color: transparent !important;
    }

    [data-testid="stChatInput"] > div {
        background-color: rgba(15, 15, 15, 0.95) !important;
        border: 1px solid #39FF14 !important;
        border-radius: 35px !important;
        box-shadow: 0 0 15px rgba(57, 255, 20, 0.4) !important;
        padding: 5px !important;
    }

    [data-testid="stChatInput"] textarea {
        background-color: transparent !important;
        color: #39FF14 !important;
        font-family: 'Courier New', monospace !important;
    }

    [data-testid="stChatInput"] button {
        background-color: transparent !important;
        color: #39FF14 !important;
        filter: drop-shadow(0 0 5px #39FF14);
    }
    [data-testid="stChatInput"] button svg { fill: #39FF14 !important; }

    [data-testid="stStatusWidget"], .stStatus {
        background-color: rgba(0, 0, 0, 0.9) !important;
        border: 1px solid #39FF14 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("📟 SYSTEM_CONTROL")
    if st.button("> CLEAR_HISTORY", use_container_width=True):
        st.session_state.messages = []
        st.session_state.processing = False
        st.session_state.logs = []
        st.session_state.graph_app = build_graph()
        st.session_state.graph_started = False
        st.session_state.awaiting_resume = False
        st.session_state.graph_done = False
        st.rerun()
    for line in st.session_state.logs:
        st.caption(f"📟 {line}")

# --- MAIN CHAT ---
col1, col2, col3 = st.columns([1, 4, 1])

with col2:
    st.title("USER@AUTO-INSTALLER:~$")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                st.markdown(msg["content"])
            else:
                st.markdown(f"> {msg['content']}")

if prompt := st.chat_input("Enter command...", disabled=st.session_state.processing):
    st.session_state.processing = True
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# --- LOGIC ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with col2:
        with st.chat_message("assistant"):
            status = st.status("EXEC_INIT...", expanded=True)
            central_feed = st.empty()
            chat_history_content = ""
            try:
                app = st.session_state.graph_app
                last_msg = st.session_state.messages[-1]["content"]

                if not st.session_state.graph_started:
                    initial_state = {
                        "task": "",
                        "to_install": [],
                        "interpreter_ready": False,
                        "task_type": None,
                        "task_medium": None,
                        "paid_preference": None,
                        "main_app_options": [],
                        "chosen_main_app": "",
                        "side_tools": [],
                        "web_options": [],
                        "installation_guides": {},
                        "installation_messages": [],
                        "messages": [HumanMessage(content=last_msg)],
                    }
                    st.session_state.graph_started = True
                    stream_iter = app.stream(initial_state, GRAPH_CONFIG)
                else:
                    stream_iter = app.stream(Command(resume=last_msg), GRAPH_CONFIG)

                for event in stream_iter:
                    for node_name, node_update in event.items():
                        status.update(label=f"RUNNING: {node_name.upper()}")
                        if not isinstance(node_update, dict):
                            continue
                        for msg in node_update.get("messages", []):
                            if isinstance(msg, AIMessage):
                                if msg.content:
                                    chat_history_content += f"\n\n> **AI:** {msg.content}"
                                for tc in (getattr(msg, "tool_calls", None) or []):
                                    chat_history_content += (
                                        f"\n\n```\n> EXEC_TOOL: {tc['name']}\n"
                                        f"> ARGS: {tc.get('args', {})}\n```"
                                    )
                            elif isinstance(msg, ToolMessage):
                                summary = str(msg.content)
                                if len(summary) > 400:
                                    summary = summary[:400] + "…"
                                chat_history_content += (
                                    f"\n\n```\n> SYSTEM_RESPONSE: {summary}\n```"
                                )
                        central_feed.markdown(chat_history_content)

                graph_state = app.get_state(GRAPH_CONFIG)

                if graph_state.next:
                    status.update(label="AWAITING_INPUT", state="running", expanded=False)
                    if not chat_history_content.strip():
                        ai_text = ""
                        for m in reversed(graph_state.values.get("messages", [])):
                            if getattr(m, "type", "") == "ai":
                                ai_text = m.content
                                break
                        if not ai_text:
                            ai_text = "Awaiting your input..."
                        chat_history_content += f"\n\n> **AI:** {ai_text}"
                    chat_history_content += "\n\n> **AWAITING_INPUT...**"
                    central_feed.markdown(chat_history_content)
                    st.session_state.messages.append({"role": "assistant", "content": chat_history_content})
                    st.session_state.awaiting_resume = True
                    st.session_state.processing = False
                    st.rerun()
                else:
                    status.update(label="EXEC_SUCCESS", state="complete", expanded=False)
                    chat_history_content += "\n\n> **EXEC_SUCCESS** — ✨ DEPLOYMENT_COMPLETE."
                    central_feed.markdown(chat_history_content)
                    st.session_state.messages.append({"role": "assistant", "content": chat_history_content})
                    st.session_state.graph_done = True
                    st.session_state.processing = False
                    st.rerun()
            except Exception as e:
                status.update(label="EXEC_FAILURE", state="error")
                st.error(f"ERR: {str(e)}")
                st.session_state.processing = False
