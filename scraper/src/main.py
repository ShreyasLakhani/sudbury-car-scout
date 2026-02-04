import time
import json
import re
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

# CONFIGURATION
TARGET_URL = "https://www.autotrader.ca/cars/on/greater%20sudbury/?rcp=15&rcs=0&srt=39&prx=50&prv=Ontario&loc=Sudbury&hprc=True&wcp=True&inMarket=advancedSearch"
OUTPUT_FILE = "cars.json"

def setup_driver():
    options = uc.ChromeOptions() 
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_argument("--mute-audio")
    driver = uc.Chrome(options=options, use_subprocess=True) 
    return driver

def extract_data_from_card(card_soup):
    """
    Extracts data from the FULL card container.
    """
    data = {}
    text_blob = card_soup.get_text(separator=' ', strip=True)
    
    # 1. PRICE
    price_match = re.search(r'\$[0-9,]+', text_blob)
    data['price'] = price_match.group(0) if price_match else "N/A"

    # 2. TITLE
    title_match = re.search(r'(19|20)\d{2}\s+[A-Za-z0-9\s\-\.]+', text_blob)
    if title_match:
        data['title'] = title_match.group(0).split('|')[0].strip()
    else:
        header = card_soup.find(['h2', 'span'], class_=lambda x: x and 'title' in x.lower())
        data['title'] = header.get_text(strip=True) if header else "N/A"

    # 3. MILEAGE
    km_matches = re.findall(r'(\d{1,3}(?:,\d{3})*|\d+)\s*km', text_blob, re.IGNORECASE)
    best_mileage = "N/A"
    
    if km_matches:
        try:
            values = [int(m.replace(',', '')) for m in km_matches]
            if values:
                max_val = max(values)
                best_mileage = f"{max_val:,} km"
        except:
            pass
    data['mileage'] = best_mileage

    # 4. LINK
    link_tag = card_soup.find('a', href=True)
    if not link_tag:
        link_tag = card_soup.find_parent('a', href=True)
    
    if link_tag and link_tag['href'].startswith('http'):
         data['link'] = link_tag['href']
    elif link_tag:
         data['link'] = "https://www.autotrader.ca" + link_tag['href']
    else:
         data['link'] = "#"

    return data

def main():
    print("--- SUDBURY CAR SCOUT: SMART CLIMBER MODE ---")
    driver = setup_driver()
    
    try:
        driver.get(TARGET_URL)
        
        print("\n" + "!"*30)
        print("ACTION REQUIRED: Solve CAPTCHA if prompted.")
        print("Press ENTER in this terminal once the page is ready.")
        print("!"*30 + "\n")
        input("Press Enter to continue...")

        print("[*] Scrolling...")
        driver.execute_script("window.scrollTo(0, 1000);")
        time.sleep(3) 

        print("[*] Analyzing Layout...")
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 1. FIND SEEDS
        seeds = soup.find_all("div", class_=lambda x: x and (
            "re-layout-inner" in x or 
            "VehicleDetailTable_container" in x or
            "listing-details" in x
        ))
        
        print(f"[*] Found {len(seeds)} layout fragments. Consolidating...")
        
        results = []
        seen_signatures = set() 

        for seed in seeds:
            working_card = seed
            found_price = False
            
            for _ in range(4):
                if "$" in working_card.get_text():
                    found_price = True
                    break
                if working_card.parent:
                    working_card = working_card.parent
            
            if not found_price:
                continue
                
            data = extract_data_from_card(working_card)
            
            if data['title'] != "N/A" and data['price'] != "N/A":
                sig = f"{data['title']}{data['price']}{data['mileage']}"
                if sig not in seen_signatures:
                    results.append(data)
                    seen_signatures.add(sig)
                    print(f" [+] Scraped: {data['title']} | {data['price']} | {data['mileage']}")

        with open(OUTPUT_FILE, "w") as f:
            json.dump(results, f, indent=2)
            print(f"\n[SUCCESS] Pipeline Output: {len(results)} cars saved to {OUTPUT_FILE}")
            
    except Exception as e:
        print(f"[!] Critical Error: {e}")
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()