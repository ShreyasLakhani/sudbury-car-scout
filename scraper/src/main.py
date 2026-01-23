import requests
from bs4 import BeautifulSoup
import sys
import time
import random

# CONFIGURATION
# use the specific Sudbury URL from AutoTrader Canada
TARGET_URL = "https://www.autotrader.ca/cars/on/greater%20sudbury/?rcp=15&rcs=0&srt=39&prx=50&prv=Ontario&loc=Sudbury&hprc=True&wcp=True&inMarket=advancedSearch"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://www.google.com/'
}

def fetch_html(url):
    try:
        time.sleep(random.uniform(2, 4))
        print(f"[*] Fetching: {url}")
        
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        if response.history:
            print(f"[!] Warning: Redirected to {response.url}")
            
        return response.text
    except Exception as e:
        print(f"[!] Error: {e}")
        return None

def analyze_page_structure(html):
    """
    Analyzes the HTML to see if data is accessible via Requests.
    """
    soup = BeautifulSoup(html, 'html.parser')
    # 1. Check for the presence of a title
    page_title = soup.title.string.strip() if soup.title else "No Title"
    print(f"[*] Page Title: {page_title}")
    
    # 2. Look for elements that typically contain listing data
    potential_listings = soup.find_all("div", class_=lambda x: x and "listing" in x)
    
    print(f"[*] Analysis: Found {len(potential_listings)} elements with 'listing' in the class name.")
    
    body_text = soup.get_text()[:500].replace('\n', ' ')
    print(f"[*] Page Snippet: {body_text}...")
    
    return len(potential_listings) > 0

def main():
    print("--- SUDBURY CAR SCOUT: PROBE MISSION ---")
    html = fetch_html(TARGET_URL)
    
    if not html:
        sys.exit(1)
        
    success = analyze_page_structure(html)
    
    if success:
        print("[+] SUCCESS: The page seems to have listing data accessible.")
    else:
        print("[-] WARNING: No listing elements found. The page might be strictly JavaScript.")

if __name__ == "__main__":
    main()