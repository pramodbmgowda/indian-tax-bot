import os
import time
from pinecone import Pinecone
from dotenv import load_dotenv

# 1. Load Secrets
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError("❌ Key not found!")

def wipe_database():
    print("⚠️ WARNING: You are about to DELETE ALL DATA from 'indian-tax-bot'.")
    confirm = input("Type 'DELETE' to confirm: ")
    
    if confirm != "DELETE":
        print("❌ Aborted.")
        return

    print("connecting to pinecone...")
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_name = "indian-tax-bot"
    
    # Check if index exists
    if index_name in [i.name for i in pc.list_indexes()]:
        index = pc.Index(index_name)
        
        # The Nuclear Option: Delete all vectors
        try:
            print("🔥 Deleting vectors...")
            index.delete(delete_all=True)
            print("✅ Database Wiped. It is now empty (0 vectors).")
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print("Index not found. Nothing to delete.")

if __name__ == "__main__":
    wipe_database()