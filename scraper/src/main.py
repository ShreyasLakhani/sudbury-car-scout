import time
import json
import re
import urllib.parse
import hashlib
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(message)s')

TARGET_URL = "https://www.autotrader.ca/cars/on/greater%20sudbury/?rcp=15&rcs=0&srt=39&prx=50&prv=Ontario&loc=Sudbury&hprc=True&wcp=True&inMarket=advancedSearch"
OUTPUT_FILE = "cars.json"

def get_driver():
    # Setup Chrome with anti-detection options
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled") 
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--mute-audio")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def clean_data(text, type="price"):
    # Extract clean numbers from text
    if type == "price":
        match = re.search(r'\$[0-9,]+', text)
        return match.group(0) if match else "N/A"
    
    matches = re.findall(r'(\d{1,3}(?:,\d{3})*|\d+)\s*km', text, re.IGNORECASE)
    if not matches: return "N/A"
    try:
        values = [int(m.replace(',', '')) for m in matches]
        return f"{max(values):,} km"
    except: return "N/A"

def parse_card(soup):
    text = soup.get_text(separator=' ', strip=True)
    data = {}

    # 1. Basic Info
    data['price'] = clean_data(text, "price")
    data['mileage'] = clean_data(text, "mileage")
    
    # 2. Find Title
    title_tag = soup.find(['h2', 'span'], class_=lambda x: x and ('title' in x.lower() or 'make-model' in x.lower()))
    data['title'] = title_tag.get_text(strip=True) if title_tag else "N/A"
    
    # Fallback if title is missing
    if data['title'] == "N/A":
        match = re.search(r'(19|20)\d{2}\s+[A-Za-z]{3,}', text)
        if match: data['title'] = match.group(0)

    # 3. Create Fallback Link (Google Search)
    # This ensures the button always works, even if AutoTrader hides the link.
    search_query = f"{data['title']} Sudbury AutoTrader"
    safe_query = urllib.parse.quote(search_query)
    unique_ref = hashlib.md5((data['title'] + data['price']).encode()).hexdigest()[:10]
    data['link'] = f"https://www.google.com/search?q={safe_query}&ref={unique_ref}"

    return data

def run_scraper():
    driver = get_driver()
    try:
        logging.info("🚀 Launching Browser...")
        driver.get(TARGET_URL)

        print("\n" + "="*40)
        print(" ACTION REQUIRED: Solve Captcha")
        print(" Press ENTER in this terminal when list loads.")
        print("="*40 + "\n")
        input("Press Enter to continue...")

        logging.info("📜 Scrolling to load more cars...")
        driver.execute_script("window.scrollTo(0, 2500);")
        time.sleep(3)

        logging.info("🔍 Parsing data...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        seeds = soup.find_all("div", class_=lambda x: x and ("re-layout-inner" in x or "listing-details" in x))
        
        results = []
        seen = set()

        for seed in seeds:
            # Climb up HTML tree to find the full card
            context = seed
            found_dollar = False
            for _ in range(4):
                if "$" in context.get_text():
                    found_dollar = True
                    break
                if context.parent: context = context.parent
            
            if not found_dollar: continue

            item = parse_card(context)

            # Save valid cars
            if item['title'] != "N/A" and item['price'] != "N/A":
                sig = f"{item['title']}-{item['price']}"
                if sig not in seen:
                    results.append(item)
                    seen.add(sig)
                    print(f" [+] Found: {item['title']} | {item['price']}")

        with open(OUTPUT_FILE, "w") as f:
            json.dump(results, f, indent=2)
        
        logging.info(f"✅ Success! Saved {len(results)} cars.")

    except Exception as e:
        logging.error(f"❌ Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_scraper()