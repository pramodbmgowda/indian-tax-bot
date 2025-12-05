import streamlit as st
import os
from pinecone import Pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import VectorStoreIndex, Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# 1. PAGE SETUP
st.set_page_config(page_title="Indian Tax AI", layout="wide")
st.title("🇮🇳 Indian Tax Law Advisor")

# 2. SECURE KEY LOADER (Works for Cloud & Local)
def get_secret(key_name):
    if key_name in st.secrets: return st.secrets[key_name]
    try:
        from dotenv import load_dotenv
        load_dotenv()
        return os.getenv(key_name)
    except: return None

google_key = get_secret("GOOGLE_API_KEY")
pinecone_key = get_secret("PINECONE_API_KEY")

if not google_key or not pinecone_key:
    st.error("🚨 Missing API Keys. Please set them in Streamlit Secrets.")
    st.stop()

# 3. INITIALIZE ENGINE (Cached for speed)
@st.cache_resource
def load_chat_engine():
    # Setup AI Models
    Settings.llm = Gemini(model="models/gemini-1.5-flash-001", api_key=google_key)
    Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Connect to Pinecone
    try:
        pc = Pinecone(api_key=pinecone_key)
        pinecone_index = pc.Index("indian-tax-bot")
        vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
        
        # Connect to existing index (Read-Only Mode)
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        
        return index.as_chat_engine(
            chat_mode="context",
            system_prompt="You are a Tax Expert. Answer strictly based on the context. If unsure, say 'I don't know'.",
            similarity_top_k=3
        )
    except Exception as e:
        st.error(f"Failed to connect to Pinecone: {e}")
        return None

if "chat_engine" not in st.session_state:
    st.session_state.chat_engine = load_chat_engine()

# 4. CHAT INTERFACE
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! Ask me about 80C, HRA, or Tax Deductions."}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Type your question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    if st.session_state.chat_engine:
        with st.chat_message("assistant"):
            with st.spinner("Analyzing Tax Rules..."):
                response = st.session_state.chat_engine.chat(prompt)
                st.write(response.response)
                st.session_state.messages.append({"role": "assistant", "content": response.response})