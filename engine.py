import os
import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

# --- 1. INTELLIGENT KEY LOADER ---
def get_key(key_name):
    try:
        return st.secrets[key_name]
    except (FileNotFoundError, KeyError):
        try:
            from dotenv import load_dotenv
            load_dotenv()
            return os.getenv(key_name)
        except ImportError:
            return None

# Fetch Keys (Global Scope)
google_key = get_key("GOOGLE_API_KEY")
pinecone_key = get_key("PINECONE_API_KEY")

if not google_key:
    st.error("🚨 Critical Error: GOOGLE_API_KEY not found. Check .env or Secrets.")
    st.stop()

# --- 2. CONFIGURE MODELS ---
# FIXED: Added "-001" to the model name to be specific and avoid the 404 error
Settings.llm = Gemini(model="models/gemini-2.0-flash", api_key=google_key)
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_chat_engine():
    if not os.path.exists("data"):
        return None

    # SCOPE FIX: Create a local variable to track which DB to use
    # We copy the global key into a local variable 'active_pinecone_key'
    active_pinecone_key = pinecone_key
    
    # --- 3. DATABASE SWITCHER ---
    
    if active_pinecone_key:
        # --- OPTION A: PINECONE (Cloud) ---
        try:
            from pinecone import Pinecone
            from llama_index.vector_stores.pinecone import PineconeVectorStore
            
            pc = Pinecone(api_key=active_pinecone_key)
            pinecone_index = pc.Index("indian-tax-bot") 
            vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            try:
                index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
            except:
                documents = SimpleDirectoryReader("./data").load_data()
                index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
                
        except Exception as e:
            # If Pinecone fails, we switch our local variable to None
            # This triggers the fallback block below
            st.warning(f"Cloud DB failed ({e}). Switching to Offline Mode.")
            active_pinecone_key = None 

    if not active_pinecone_key:
        # --- OPTION B: CHROMADB (Local) ---
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