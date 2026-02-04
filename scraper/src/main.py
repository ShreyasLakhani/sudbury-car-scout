import time
import json
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import os

# CONFIGURATION
TARGET_URL = "https://www.autotrader.ca/cars/on/greater%20sudbury/?rcp=15&rcs=0&srt=39&prx=50&prv=Ontario&loc=Sudbury&hprc=True&wcp=True&inMarket=advancedSearch"

def setup_driver():
    options = uc.ChromeOptions() 
    driver = uc.Chrome(options=options, use_subprocess=True) 
    return driver

def parse_listing(card_soup):
    data = {}
    
    # Title
    title_tag = card_soup.find('span', class_='result-title')
    if not title_tag:
        title_tag = card_soup.find('h2')
    data['title'] = title_tag.get_text(strip=True) if title_tag else "N/A"

    # Regex Parsing
    text_blob = card_soup.get_text(separator=' ', strip=True)
    
    # Price
    price_match = re.search(r'\$[0-9,]+', text_blob)
    data['price'] = price_match.group(0) if price_match else "N/A"

    # Mileage
    odo_match = re.search(r'(\d{1,3}(?:,\d{3})*|\d+)\s*km', text_blob)
    data['mileage'] = odo_match.group(0) if odo_match else "N/A"
    
    # Link
    link_tag = card_soup.find('a', href=True)
    data['link'] = "https://www.autotrader.ca" + link_tag['href'] if link_tag else "N/A"
    
    return data

def main():
    print("--- SUDBURY CAR SCOUT: LIVE EXTRACTION ---")
    driver = setup_driver()
    
    try:
        driver.get(TARGET_URL)
        
        # === HUMAN HANDOVER ===
        print("\n" + "!"*30)
        print("WAITING FOR HUMAN: Solve CAPTCHA if needed.")
        print("Press ENTER once cars are visible.")
        print("!"*30 + "\n")
        input("Press Enter to continue...")
        # ======================

        print("[*] Scrolling...")
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(3) 

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        listings = soup.find_all("div", class_=lambda x: x and "listing" in x)
        
        valid_listings = [l for l in listings if len(l.get_text(strip=True)) > 50]
        
        print(f"[*] Processing {len(valid_listings)} containers...")
        
        results = []
        seen_titles = set() # For deduplication

        for card in valid_listings:
            car = parse_listing(card)
            
            # QUALITY CONTROL FILTERS:
            # 1. Must have a valid Title
            # 2. Must have a valid Price (removes the N/A duplicates)
            # 3. Must not be a duplicate we already saved
            
            if car['title'] != "N/A" and car['price'] != "N/A":
                unique_id = f"{car['title']}-{car['price']}"
                
                if unique_id not in seen_titles:
                    results.append(car)
                    seen_titles.add(unique_id)
                    print(f" [+] {car['title']} | {car['price']} | {car['mileage']}")

        # Save to JSON
        with open("cars.json", "w") as f:
            json.dump(results, f, indent=2)
            print(f"\n[SUCCESS] Saved {len(results)} unique vehicles to cars.json")
            
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()