import os
from dotenv import load_dotenv  # <--- NEW IMPORT

# 1. LOAD THE KEYS
# This looks for a .env file and loads variables into the system
load_dotenv()

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore

# 2. USE THE KEYS SECURELY
# Instead of pasting the key string, we fetch it from the system
google_key = os.getenv("GOOGLE_API_KEY")

if not google_key:
    raise ValueError("GOOGLE_API_KEY not found! Did you create the .env file?")

# Configure Gemini with the secure key
Settings.llm = Gemini(model="models/gemini-2.0-flash", api_key=google_key)
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

def get_chat_engine():
    # ... rest of your code remains exactly the same ...
    # (Checking data, Loading ChromaDB, etc.)
    
    # Just ensure you use the secure 'Settings' we configured above
    
    if not os.path.exists("data"):
        return None

    db = chromadb.PersistentClient(path="./chroma_db")
    chroma_collection = db.get_or_create_collection("indian_tax_law")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    documents = SimpleDirectoryReader("./data").load_data()
    index = VectorStoreIndex.from_documents(documents, storage_context=storage_context)

    chat_engine = index.as_chat_engine(
        chat_mode="context",
        memory=None,
        system_prompt=(
            "You are an Indian Tax Law Expert. "
            "Answer strictly based on the context provided."
        ),
        similarity_top_k=3
    )
    
    return chat_engine