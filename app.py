import streamlit as st
import os
import uuid
from pinecone import Pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from dotenv import load_dotenv

# ---------------------------------------------------------
# 1. CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="TaxBot Pro",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

load_dotenv()

# ---------------------------------------------------------
# 2. SAFE SECRET LOADER
# ---------------------------------------------------------
def get_key(k):
    try:
        if hasattr(st, "secrets") and len(st.secrets) > 0:
            return st.secrets.get(k)
    except:
        pass
    return os.getenv(k)

GOOGLE_API_KEY = get_key("GOOGLE_API_KEY")
PINECONE_API_KEY = get_key("PINECONE_API_KEY")

if not GOOGLE_API_KEY or not PINECONE_API_KEY:
    st.error("🚨 Missing API keys. Add them in .env or .streamlit/secrets.toml")
    st.stop()

# ---------------------------------------------------------
# 3. CSS (Sidebar visible, toggle restored)
# ---------------------------------------------------------
st.markdown("""
<style>

.stApp {
    background-color: #0e1117;
    font-family: 'Roboto', sans-serif;
}

/* SIDEBAR BG */
[data-testid="stSidebar"] {
    background-color: #161b22 !important;
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] * {
    color: #f0f6fc !important;
}

/* SIDEBAR BUTTONS */
.sidebar-btn > button {
    width: 100%;
    background-color: #21262d !important;
    border: 1px solid #30363d !important;
    color: #c9d1d9 !important;
    padding: 10px;
    border-radius: 6px;
    text-align: left;
    font-weight: 500;
}
.sidebar-btn > button:hover {
    border-color: #58a6ff !important;
    color: #58a6ff !important;
}

/* Chat bubbles */
.stChatMessage {
    border-radius: 10px;
    padding: 15px;
    border: 1px solid #30363d;
    margin-bottom: 10px;
}
.stChatMessage.user {
    background-color: #1f2428;
    border-left: 4px solid #58a6ff;
}
.stChatMessage.assistant {
    background-color: #161b22;
}

/* Chat input */
.stChatInput textarea {
    background-color: #0d1117 !important;
    border: 1px solid #30363d !important;
    color: white !important;
    border-radius: 8px !important;
}
.stChatInput textarea:focus {
    border-color: #58a6ff !important;
}

/* IMPORTANT: DO NOT HIDE HEADER → Sidebar toggle stays visible */
#MainMenu, footer {visibility: hidden;}

</style>
""", unsafe_allow_html=True)

# Ensure sidebar never collapses
st.sidebar.markdown(
    "<style>div[data-testid='stSidebar'] {min-width: 300px !important;}</style>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 4. LOAD ENGINE
# ---------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_engine():
    try:
        Settings.llm = Gemini(model="gemini-2.0-flash", api_key=GOOGLE_API_KEY)
        Settings.embed_model = HuggingFaceEmbedding("sentence-transformers/all-MiniLM-L6-v2")

        pc = Pinecone(api_key=PINECONE_API_KEY)
        pinecone_index = pc.Index("indian-tax-bot")

        vstore = PineconeVectorStore(pinecone_index=pinecone_index)
        idx = VectorStoreIndex.from_vector_store(vstore)

        return idx.as_chat_engine(
            chat_mode="context",
            system_prompt="Expert Indian Tax Advisor. Answer concisely using retrieved context only.",
            similarity_top_k=5
        )
    except Exception as e:
        st.error(f"Engine init failed: {e}")
        return None

# ---------------------------------------------------------
# 5. SESSION STORE
# ---------------------------------------------------------
if "chat_store" not in st.session_state:
    st.session_state.chat_store = {}

if "active_id" not in st.session_state:
    cid = str(uuid.uuid4())
    st.session_state.active_id = cid
    st.session_state.chat_store[cid] = {"title": "New Session", "msgs": []}


def new_chat():
    cid = str(uuid.uuid4())
    st.session_state.chat_store[cid] = {"title": "New Session", "msgs": []}
    st.session_state.active_id = cid


def clear_all():
    st.session_state.chat_store = {}
    new_chat()

# ---------------------------------------------------------
# 6. SIDEBAR WITH HISTORY
# ---------------------------------------------------------
with st.sidebar:
    st.header("🗂️ Chat History")

    # NEW CHAT button
    with st.container():
        st.markdown('<div class="sidebar-btn">', unsafe_allow_html=True)
        if st.button("➕ Start New Chat", use_container_width=True):
            new_chat()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # CHAT LIST
    for sid, data in reversed(list(st.session_state.chat_store.items())):
        title = data["title"][:25] + ("..." if len(data["title"]) > 25 else "")
        label = ("🟢 " if sid == st.session_state.active_id else "📄 ") + title

        with st.container():
            st.markdown('<div class="sidebar-btn">', unsafe_allow_html=True)
            if st.button(label, key=sid, use_container_width=True):
                st.session_state.active_id = sid
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    # CLEAR ALL
    with st.container():
        st.markdown('<div class="sidebar-btn">', unsafe_allow_html=True)
        if st.button("⚠️ Clear All Sessions", use_container_width=True):
            clear_all()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# 7. MAIN CHAT AREA
# ---------------------------------------------------------
st.title("Indian Tax Advisor")

engine = get_engine()
chat = st.session_state.chat_store[st.session_state.active_id]

# Intro card
if not chat["msgs"]:
    st.markdown("""
    <div style='background:#161b22; padding:20px; border-radius:8px; border:1px solid #30363d;'>
        <h3 style='color:#58a6ff;'>Welcome!</h3>
        <p>Ask anything about <b>Indian Income Tax</b>.</p>
        <p>Try: <b>“What is Section 80C?”</b></p>
    </div>
    """, unsafe_allow_html=True)

# Display chat history
for msg in chat["msgs"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("Sources"):
                for s in msg["sources"]:
                    st.markdown(f"- {s}")

# ---------------------------------------------------------
# 8. INPUT HANDLER
# ---------------------------------------------------------
prompt = st.chat_input("Ask your tax question...")

if prompt:
    if not chat["msgs"]:
        chat["title"] = prompt[:50]

    chat["msgs"].append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        response_text = ""

        try:
            if engine:
                resp = engine.stream_chat(prompt)

                for token in resp.response_gen:
                    response_text += token
                    placeholder.markdown(response_text + "▌")

                placeholder.markdown(response_text)

                # Attach sources
                sources = []
                if hasattr(resp, "source_nodes"):
                    for node in resp.source_nodes:
                        if node.score > 0.65:
                            sources.append(
                                f"{node.metadata.get('file_name', 'Doc')}: {node.get_content()[:80]}..."
                            )

                chat["msgs"].append({
                    "role": "assistant",
                    "content": response_text,
                    "sources": sources
                })

                if len(chat["msgs"]) == 2:
                    st.rerun()

        except Exception as e:
            st.error(f"Chat Error: {e}")