import os
import streamlit as st
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

# --- 1. INTELLIGENT KEY LOADER ---
# This function looks for keys in Streamlit Secrets (Cloud) FIRST.
# If not found, it looks in .env (Local).
def get_key(key_name):
    try:
        return st.secrets[key_name]
    except (FileNotFoundError, KeyError):
        # We are likely running locally
        try:
            from dotenv import load_dotenv
            load_dotenv()
            return os.getenv(key_name)
        except ImportError:
            return None

# Fetch Keys
google_key = get_key("GOOGLE_API_KEY")
pinecone_key = get_key("PINECONE_API_KEY") # Optional for now

if not google_key:
    st.error("🚨 Critical Error: GOOGLE_API_KEY not found. Please set it in .env (Local) or Streamlit Secrets (Cloud).")
    st.stop()

# --- 2. CONFIGURE MODELS ---
# Using 1.5-flash as it is currently the most stable for LlamaIndex. 
# You can try "models/gemini-2.0-flash-exp" if you have access.
Settings.llm = Gemini(model="models/gemini-1.5-flash", api_key=google_key)
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_chat_engine():
    if not os.path.exists("data"):
        return None

    # --- 3. DATABASE SWITCHER (Local vs. Cloud) ---
    # Ideally, use Pinecone for Cloud. Use Chroma for Local.
    
    if pinecone_key:
        # --- OPTION A: PINECONE (Cloud Standard) ---
        try:
            from pinecone import Pinecone
            from llama_index.vector_stores.pinecone import PineconeVectorStore
            
            pc = Pinecone(api_key=pinecone_key)
            # Create index "indian-tax-bot" in Pinecone dashboard first!
            pinecone_index = pc.Index("indian-tax-bot") 
            vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
            storage_context = StorageContext.from_defaults(vector_store=vector_store)
            
            # Try to load existing index (Fast)
            try:
                index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
            except:
                # If empty, load data
                documents = SimpleDirectoryReader("./data").load_data()
                index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)
                
        except Exception as e:
            st.warning(f"Pinecone connection failed ({e}). Falling back to ChromaDB.")
            # Fallback to Option B
            pinecone_key = None 

    if not pinecone_key:
        # --- OPTION B: CHROMADB (Local / Temporary) ---
        # Note: On Streamlit Cloud, this data disappears on reboot.
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