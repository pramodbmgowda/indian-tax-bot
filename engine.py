import os
import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from pinecone import Pinecone
from llama_index.vector_stores.pinecone import PineconeVectorStore
from dotenv import load_dotenv
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

# Load Local Keys from .env
load_dotenv()

# --- 1. BULLETPROOF KEY LOADER ---
def get_key(key_name):
    # 1. Try Local .env FIRST (Safest for local dev)
    local_key = os.getenv(key_name)
    if local_key:
        return local_key

    # 2. Try Streamlit Secrets (Cloud)
    # We wrap this in a try-block because accessing st.secrets crashes 
    # if the file doesn't exist on your computer.
    try:
        if key_name in st.secrets:
            return st.secrets[key_name]
    except Exception:
        return None
    
    return None

# Fetch Keys
google_key = get_key("GOOGLE_API_KEY")
pinecone_key = get_key("PINECONE_API_KEY")

if not google_key:
    st.error("🚨 Critical Error: GOOGLE_API_KEY not found. Check your .env file.")
    st.stop()

# --- 2. CONFIGURE MODELS ---
# Using the specific -001 model to avoid Google API 404 errors
Settings.llm = Gemini(model="models/gemini-2.0-flash", api_key=google_key)
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_chat_engine():
    if not os.path.exists("data"):
        return None

    active_pinecone_key = pinecone_key
    
    # --- 3. DATABASE SWITCHER ---
    
    if active_pinecone_key:
        # --- OPTION A: PINECONE (Cloud) ---
        try:
            pc = Pinecone(api_key=active_pinecone_key)
            pinecone_index = pc.Index("indian-tax-bot") 
            vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # Check if index is empty
            stats = pinecone_index.describe_index_stats()
            if stats.total_vector_count == 0:
                documents = SimpleDirectoryReader("./data").load_data()
                index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
            else:
                index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
                
        except Exception as e:
            st.warning(f"Cloud DB failed ({e}). Switching to Offline Mode.")
            active_pinecone_key = None 

    if not active_pinecone_key:
        # --- OPTION B: CHROMADB (Local Backup) ---
        db = chromadb.PersistentClient(path="./chroma_db")
        chroma_collection = db.get_or_create_collection("indian_tax_law")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        documents = SimpleDirectoryReader("./data").load_data()
        index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)

    # --- 4. CHAT ENGINE ---
    chat_engine = index.as_chat_engine(
        chat_mode="context",
        system_prompt=(
            "You are an Indian Tax Law Expert. "
            "Answer strictly based on the context provided. "
            "If the answer is not in the context, say you don't know."
        ),
        similarity_top_k=3
    )
    
    return chat_engine