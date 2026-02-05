import time
import json
import re
import os
import logging
import urllib.parse
import hashlib
from bs4 import BeautifulSoup

# Standard Selenium Imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TARGET_URL = "https://www.autotrader.ca/cars/on/greater%20sudbury/?rcp=15&rcs=0&srt=39&prx=50&prv=Ontario&loc=Sudbury&hprc=True&wcp=True&inMarket=advancedSearch"
OUTPUT_FILE = "cars.json"

def get_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled") 
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--mute-audio")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def clean_price(text):
    match = re.search(r'\$[0-9,]+', text)
    return match.group(0) if match else "N/A"

def clean_mileage(text):
    matches = re.findall(r'(\d{1,3}(?:,\d{3})*|\d+)\s*km', text, re.IGNORECASE)
    if not matches: return "N/A"
    try:
        values = [int(m.replace(',', '')) for m in matches]
        return f"{max(values):,} km"
    except: return "N/A"

def parse_card(soup):
    text = soup.get_text(separator=' ', strip=True)
    data = {}

    # 1. Price
    data['price'] = clean_price(text)

    # 2. Title
    data['title'] = "N/A"
    title_tag = soup.find(['h2', 'span'], class_=lambda x: x and ('title' in x.lower() or 'make-model' in x.lower()))
    if title_tag:
        data['title'] = title_tag.get_text(strip=True)
    
    # Fallback Title
    if data['title'] == "N/A":
        title_match = re.search(r'(19|20)\d{2}\s+[A-Za-z]{3,}', text)
        if title_match:
            data['title'] = title_match.group(0)

    if "finance" in data['title'].lower() or "credit" in data['title'].lower():
        data['title'] = "N/A"

    # 3. Link (With Google Fallback)
    real_link = "#"
    all_links = soup.find_all('a', href=True)
    
    for a in all_links:
        href = a['href']
        if href != "#" and ("/a/" in href or "/cars/" in href or "detail" in href):
             real_link = href if href.startswith('http') else f"https://www.autotrader.ca{href}"
             break
    
    if real_link == "#" and data['title'] != "N/A":
        search_query = f"{data['title']} Sudbury AutoTrader"
        safe_query = urllib.parse.quote(search_query)
        unique_hash = hashlib.md5((data['title'] + data['price']).encode()).hexdigest()[:10]
        real_link = f"https://www.google.com/search?q={safe_query}&ref={unique_hash}"

    data['link'] = real_link

    # 4. Mileage
    data['mileage'] = clean_mileage(text)

    return data

def run_scraper():
    driver = None
    try:
        logging.info("Launching Chrome...")
        driver = get_driver()
        driver.get(TARGET_URL)

        print("\n" + "="*40)
        print(" ACTION REQUIRED: Solve Captcha")
        print(" Press ENTER when the list is visible.")
        print("="*40 + "\n")
        input("Press Enter to continue...")

        logging.info("Scrolling...")
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, 2500);")
        time.sleep(3)

        logging.info("Parsing...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        seeds = soup.find_all("div", class_=lambda x: x and (
            "re-layout-inner" in x or 
            "VehicleDetailTable_container" in x or
            "listing-details" in x
        ))

        logging.info(f"Found {len(seeds)} layout fragments. Climbing tree...")

        results = []
        seen = set()

        for seed in seeds:
            context = seed
            found_dollar = False
            for _ in range(4):
                if "$" in context.get_text():
                    found_dollar = True
                    break
                if context.parent:
                    context = context.parent
            
            if not found_dollar: continue

            item = parse_card(context)

            if item['title'] != "N/A" and item['price'] != "N/A":
                sig = f"{item['title']}-{item['price']}"
                if sig not in seen:
                    results.append(item)
                    seen.add(sig)
                    print(f" [+] Found: {item['title']} | {item['price']}")

        with open(OUTPUT_FILE, "w") as f:
            json.dump(results, f, indent=2)
        
        logging.info(f"Success! Saved {len(results)} valid cars.")

    except Exception as e:
        logging.error(f"Scraper failed: {e}")
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    run_scraper()