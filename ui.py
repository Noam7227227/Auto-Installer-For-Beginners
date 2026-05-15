import streamlit as st
import urllib.parse
import datetime
import time
from src.graph import build_graph

st.set_page_config(page_title="Terminal_Terminal", page_icon="📟", layout="wide")

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False

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
        background-color: transparent !important; /* Hide the outer wrapper */
    }

    [data-testid="stChatInput"] > div {
        background-color: rgba(15, 15, 15, 0.95) !important;
        border: 1px solid #39FF14 !important;
        border-radius: 35px !important; /* Forces the pill shape */
        box-shadow: 0 0 15px rgba(57, 255, 20, 0.4) !important;
        padding: 5px !important;
    }

    /* Ensure the text area itself doesn't have a background */
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
        st.rerun()

# --- MAIN CHAT ---
col1, col2, col3 = st.columns([1, 4, 1])

with col2:
    st.title("USER@AUTO-INSTALLER:~$")
    
    # History
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(f"> {msg['content']}")

# Input (pinned to bottom)
if prompt := st.chat_input("Enter command...", disabled=st.session_state.processing):
    st.session_state.processing = True
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

# --- LOGIC ---
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    with col2:
        with st.chat_message("assistant"):
            status = st.status("EXEC_INIT...", expanded=True)
            try:
                app = build_graph()
                last_msg = st.session_state.messages[-1]["content"]
                for event in app.stream({"task": last_msg, "messages": []}):
                    for node_name, _ in event.items():
                        status.update(label=f"RUNNING: {node_name.upper()}")
                
                status.update(label="EXEC_SUCCESS", state="complete", expanded=False)
                final_text = "✨ DEPLOYMENT_COMPLETE."
                st.markdown(final_text)
                
                st.session_state.messages.append({"role": "assistant", "content": final_text})
                st.session_state.processing = False
                st.rerun()
            except Exception as e:
                status.update(label="EXEC_FAILURE", state="error")
                st.error(f"ERR: {str(e)}")
                st.session_state.processing = False
                