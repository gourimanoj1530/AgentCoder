import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AgentCoder",
    page_icon="🤖",
    layout="wide",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .stApp { background-color: #0f1117; }
    .main-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00d2ff, #7b2ff7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .subtitle {
        color: #888;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .stat-box {
        background: #1e1e2e;
        border: 1px solid #2e2e3e;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: #00d2ff;
    }
    .stat-label {
        color: #888;
        font-size: 0.85rem;
    }
    .error-box {
        background: #2a1a1a;
        border-left: 3px solid #ff4b4b;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin-top: 0.5rem;
        font-size: 0.85rem;
        color: #ffaaaa;
    }
    .chat-user {
        background: #1a1a2e;
        border-radius: 12px 12px 4px 12px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        color: #e0e0e0;
        border: 1px solid #2e2e4e;
    }
    .chat-agent {
        background: #0d2137;
        border-radius: 12px 12px 12px 4px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border: 1px solid #1a3a5c;
        color: #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">🤖 AgentCoder</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Agentic AI coding assistant · LangGraph + Groq · ReAct loop</div>', unsafe_allow_html=True)

# ─── Session state ────────────────────────────────────────────────────────────

if "history" not in st.session_state:
    st.session_state.history = []  # List of {role, content, steps, errors}

if "total_queries" not in st.session_state:
    st.session_state.total_queries = 0

if "total_steps" not in st.session_state:
    st.session_state.total_steps = 0

# ─── Layout ───────────────────────────────────────────────────────────────────

left_col, right_col = st.columns([3, 1])

with right_col:
    st.markdown("### 📊 Session Stats")
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-value">{st.session_state.total_queries}</div>
        <div class="stat-label">Queries</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("")
    st.markdown(f"""
    <div class="stat-box">
        <div class="stat-value">{st.session_state.total_steps}</div>
        <div class="stat-label">Total ReAct Steps</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("")

    # Health check
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        if r.status_code == 200:
            st.success("API online")
        else:
            st.error("API error")
    except Exception:
        st.error("API offline — start uvicorn first")

    st.markdown("---")
    if st.button("🗑️ Clear history"):
        st.session_state.history = []
        st.session_state.total_queries = 0
        st.session_state.total_steps = 0
        st.rerun()

with left_col:
    # ── Chat history ──────────────────────────────────────────────────────────
    chat_container = st.container()

    with chat_container:
        for msg in st.session_state.history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">💬 <b>You:</b> {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-agent">🤖 <b>AgentCoder</b> · {msg["steps"]} ReAct steps</div>', unsafe_allow_html=True)
                st.markdown(msg["content"])

                if msg.get("errors"):
                    with st.expander(f"⚠️ {len(msg['errors'])} error(s) encountered"):
                        for e in msg["errors"]:
                            st.markdown(f'<div class="error-box">{e}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── Input ─────────────────────────────────────────────────────────────────
    with st.form("input_form", clear_on_submit=True):
        user_input = st.text_area(
            "Describe your coding problem:",
            placeholder="e.g. Write a Python function to find all permutations of a string",
            height=100,
        )
        submitted = st.form_submit_button("🚀 Run Agent", use_container_width=True)

    if submitted and user_input.strip():
        # Add user message to history
        st.session_state.history.append({
            "role": "user",
            "content": user_input.strip(),
        })

        with st.spinner("🔄 Agent is thinking... (ReAct loop running)"):
            try:
                response = requests.post(
                    f"{API_URL}/run",
                    json={"problem": user_input.strip()},
                    timeout=120,
                )
                data = response.json()

                if response.status_code == 200:
                    st.session_state.history.append({
                        "role": "agent",
                        "content": data["answer"],
                        "steps": data["steps_taken"],
                        "errors": data.get("errors", []),
                    })
                    st.session_state.total_queries += 1
                    st.session_state.total_steps += data["steps_taken"]
                else:
                    st.error(f"API error: {data.get('detail', 'Unknown error')}")

            except requests.exceptions.Timeout:
                st.error("Request timed out. The agent took too long — try a simpler problem.")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Make sure uvicorn is running.")
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")

        st.rerun()