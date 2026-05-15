import streamlit as st
import urllib.parse
from src.graph import build_graph

st.set_page_config(page_title="Terminal_Terminal", page_icon="📟", layout="wide")

# --- BACKGROUND ANIMATION (HORIZONTAL BINARY STREAM) ---
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
        if (frameCount % 6 !== 0) { 
            requestAnimationFrame(draw);
            return;
        }

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

# Encode the HTML and set height to 1 to satisfy Streamlit's validation
encoded_html = urllib.parse.quote(binary_html)
st.iframe(src=f"data:text/html;charset=utf-8,{encoded_html}", height=1)

# --- HACKER UI STYLING (CSS) ---
st.markdown("""
<style>
    /* Pin the animation iframe to the background */
    iframe {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw !important;
        height: 100vh !important;
        z-index: -1;
        border: none;
        pointer-events: none;
        opacity: 0.2;
    }

    /* Force full transparency on Streamlit containers */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMainViewContainer"], 
    [data-testid="stHeader"], [data-testid="stToolbar"], .main {
        background-color: transparent !important;
    }

    body {
        background-color: #000000 !important;
    }

    /* Terminal Text Styling */
    .stMarkdown p, h1, h2, h3, label, .stChatMessage p {
        color: #39FF14 !important;
        text-shadow: 0 0 5px rgba(57, 255, 20, 0.8);
        font-family: 'Courier New', monospace !important;
    }

    /* Icon Font Safeguard */
    [data-testid="stIcon"], .notranslate, [class^="st-icon-"] {
        font-family: inherit !important;
        text-shadow: none !important;
    }

    /* Sidebar terminal look */
    [data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.85) !important;
        border-right: 1px solid #39FF14;
    }

    /* Darker Chat Messages */
    .stChatMessage {
        background: rgba(0, 0, 0, 0.7) !important;
        border: 1px solid #39FF14 !important;
        border-radius: 8px !important;
    }

    /* Chat Input Styling */
    [data-testid="stChatInput"] {
        background-color: rgba(0, 0, 0, 0.9) !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    [data-testid="stChatInput"] textarea {
        color: #39FF14 !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* Neon Green Submit Arrow */
    [data-testid="stChatInput"] button {
        background-color: transparent !important;
        border: none !important;
        color: #39FF14 !important;
        filter: drop-shadow(0 0 5px rgba(57, 255, 20, 0.8));
    }
    
    [data-testid="stChatInput"] button svg {
        fill: #39FF14 !important;
    }

    /* Status Box styling */
    .stStatus {
        background-color: rgba(0, 0, 0, 0.8) !important;
        border: 1px solid #39FF14 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("📟 SYSTEM_CONTROL")
    if st.button("> CLEAR_HISTORY", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    st.warning("NOTICE: ADMIN PRIVILEGES REQUIRED")

# --- MAIN CHAT INTERFACE ---
col1, col2, col3 = st.columns([1, 4, 1])

with col2:
    st.title("USER@AUTO-INSTALLER:~$")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(f"> {msg['content']}")

    if prompt := st.chat_input("Enter command..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(f"> {prompt}")

        with st.chat_message("assistant"):
            status = st.status("EXEC_INIT...", expanded=True)
            try:
                app = build_graph()
                initial_state = {"task": prompt, "to_install": [], "messages": []}
                
                for event in app.stream(initial_state, {"recursion_limit": 50}):
                    for node_name, node_update in event.items():
                        status.update(label=f"RUNNING: {node_name.upper()}")
                
                status.update(label="EXEC_SUCCESS", state="complete", expanded=False)
                final_text = "✨ DEPLOYMENT_COMPLETE."
                st.markdown(final_text)
                st.session_state.messages.append({"role": "assistant", "content": final_text})
            except Exception as e:
                status.update(label="EXEC_FAILURE", state="error")
                st.error(f"ERR: {str(e)}")