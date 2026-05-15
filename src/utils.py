import streamlit as st

try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
except Exception:
    get_script_run_ctx = None


def _in_streamlit() -> bool:
    if get_script_run_ctx is None:
        return False
    try:
        return get_script_run_ctx() is not None
    except Exception:
        return False


def ui_log(message: str):
    if not _in_streamlit():
        print(message)
        return
    try:
        if "logs" not in st.session_state:
            st.session_state.logs = []
        st.session_state.logs.append(message)
        st.sidebar.caption(f"📟 {message}")
    except Exception:
        print(message)
