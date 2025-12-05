import os
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.core import VectorStoreIndex, StorageContext, Document, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from curl_cffi import requests as cffi_requests

# 1. LOAD SECRETS
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not PINECONE_API_KEY:
    raise ValueError("❌ PINECONE_API_KEY not found. Check your .env file.")

# 2. SETUP EMBEDDING MODEL
print("⚙️ Loading Embedding Model...")
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 3. ROBUST SCRAPER
def scrape_url(url):
    try:
        # We use a randomized browser impersonation to avoid detection
        response = cffi_requests.get(
            url, 
            impersonate="chrome110", 
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"   ⚠️ Blocked (Status {response.status_code}) for {url}")
            return None
            
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Smart Extraction: Covers IndiaFilings, BankBazaar, Tax2Win, Wiki
        content = (
            soup.find('div', class_='entry-content') or   # IndiaFilings
            soup.find('div', class_='bank-news-post') or # BankBazaar
            soup.find('div', class_='story_content') or  # Tax2Win
            soup.find('div', {'id': 'bodyContent'}) or   # Wiki
            soup.find('article') or 
            soup.find('body')
        )
        
        if not content:
            return None
        
        # Cleaning
        text = content.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 50]
        return "\n".join(lines[:200]) # Keep top 200 lines
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

# 4. DATA PIPELINE
def run_pipeline():
    # STRATEGY: Distributed Sources to avoid Rate Limiting
    sources = [
        # Source 1: IndiaFilings (Worked for 80C, so we keep it)
        {"title": "Section 80C Deductions", "url": "https://www.indiafilings.com/learn/section-80c-deduction/"},
        
        # Source 2: BankBazaar (Excellent for 80D & HRA, very bot-friendly)
        {"title": "Section 80D Medical", "url": "https://www.bankbazaar.com/tax/section-80d.html"},
        {"title": "HRA Exemptions", "url": "https://www.bankbazaar.com/tax/house-rent-allowance.html"},
        
        # Source 3: Tax2Win (Great for Home Loans)
       # Change this line in your sources list:
     # Replace the failed line with this working URL:
{"title": "Home Loan Tax Benefits", "url": "https://www.bajajfinserv.in/tax-deduction-on-home-loan-interest-under-section-24"},
        {"title": "Income Tax India (Wiki Backup)", "url": "https://en.wikipedia.org/wiki/Income_tax_in_India"},
        
    ]

    documents = []
    print("🚀 Starting Distributed Data Pipeline...")
    
    for source in sources:
        print(f"   ⬇️ Scraping: {source['title']}...")
        text = scrape_url(source['url'])
        
        if text:
            print(f"      ✅ Success! ({len(text)} chars)")
            doc = Document(text=text, metadata={"source": source['url'], "title": source['title']})
            documents.append(doc)
            time.sleep(3) # Wait 3 seconds between requests to be safe
        else:
            print("      ❌ Failed.")

    if not documents:
        print("❌ CRITICAL: No data scraped.")
        return

    print(f"\n☁️ Uploading {len(documents)} documents to Pinecone...")
    
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index_name = "indian-tax-bot"
    
    # Auto-create Index
    if index_name not in [i.name for i in pc.list_indexes()]:
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    
    pinecone_index = pc.Index(index_name)
    vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    VectorStoreIndex.from_documents(documents, storage_context=storage_context)
    
    print("✅ Pipeline Success! Data is live in the Cloud.")

if __name__ == "__main__":
    run_pipeline()