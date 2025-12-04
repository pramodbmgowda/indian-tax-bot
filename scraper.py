import os
import time
import requests
from bs4 import BeautifulSoup

# Setup Data Directory
if not os.path.exists("data"):
    os.makedirs("data")

def clean_text(html):
    soup = BeautifulSoup(html, "html.parser")
    # IndianKanoon stores the actual law text inside a div class called 'judgments' or 'doc_content'
    # We strip out the ads and navigation
    content = soup.find('div', class_='doc_content')
    if content:
        return content.get_text(separator="\n").strip()
    return soup.get_text(separator="\n").strip()

def scrape_indian_kanoon():
    print("🚀 Initializing Scraper (Target: IndianKanoon)...")
    
    # We define the URLs for the specific "Gold Standard" sections manually 
    targets = [
        {"section": "Section_80C", "url": "https://indiankanoon.org/doc/1447833/"},
        {"section": "Section_80D", "url": "https://indiankanoon.org/doc/1429896/"},
        {"section": "Section_10_HRA", "url": "https://indiankanoon.org/doc/1183311/"},
        {"section": "Section_24_House_Prop", "url": "https://indiankanoon.org/doc/170997/"},
        {"section": "Section_139_Returns", "url": "https://indiankanoon.org/doc/1066741/"}
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
    }

    print(f"📋 Found {len(targets)} critical sections to scrape.")

    for i, target in enumerate(targets):
        title = target['section']
        url = target['url']
        
        print(f"   ⬇️ [{i+1}/{len(targets)}] Downloading: {title}...")
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                content = clean_text(response.content)
                
                # Save to file
                filename = f"data/{title}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"SOURCE: {url}\n")
                    f.write(f"SECTION: {title}\n\n")
                    f.write(content)
            else:
                print(f"      ❌ Failed (Status {response.status_code})")

        except Exception as e:
            print(f"      ❌ Error: {e}")
        
        # CRITICAL: Be polite. IndianKanoon bans IPs that scrape too fast.
        time.sleep(2) 

    print("🎉 Scraping Complete! Data saved in /data folder.")

if __name__ == "__main__":
    scrape_indian_kanoon()