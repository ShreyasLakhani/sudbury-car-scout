import requests
from bs4 import BeautifulSoup
import sys
import time

# 1. CONSTANTS
# We use a real browser User-Agent. 
# "Sudbury Car Scout" processes 500+ listings[cite: 29], so we must look like a human, not a bot.
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_page(url):
    """
    Fetches HTML content with error handling.
    This fulfills the "efficient error handling mechanisms" claim.
    """
    try:
        print(f"[*] Connecting to: {url}")
        # Timeout is crucial so the pipeline doesn't hang forever
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status() 
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"[!] Network Error: {e}")
        return None

def parse_test_data(html):
    """
    Simple parser to verify BeautifulSoup is working before we target AutoTrader.
    """
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.title.string if soup.title else "No Title"
    return title

def main():
    # PHASE 1: Connection Test
    # We test with a static site first to prove the pipeline works.
    target_url = "https://example.com"
    
    html = fetch_page(target_url)
    
    if html:
        print("[*] Page fetched successfully.")
        data = parse_test_data(html)
        print(f"[+] Extracted Title: {data}")
    else:
        print("[!] Pipeline failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()