"""
Verkaufen.de Preis-Crawler v5.0 - Vollständig
Mit allen 837 Produkten
"""

import pandas as pd
import time
import random
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

INPUT_FILE = "F:/crawlerv5/RELEASE.xlsx"
OUTPUT_FILE = "F:/crawlerv5/RELEASE_ergebnis.xlsx"
VERKAUFEN_BASE = "https://www.verkaufen.de"

MIN_PAUSE = 2
MAX_PAUSE = 5


def human_pause():
    time.sleep(random.uniform(MIN_PAUSE, MAX_PAUSE))


def extract_all_from_url(url):
    match = re.search(r'net/([a-z0-9-]+)_h_', url)
    if not match:
        return None, None, None, None
    
    name = match.group(1)
    parts = name.split('-')
    
    brand = parts[0]
    model = None
    gb = None
    color = None
    
    color_map = {
        'blau': 'Blau',
        'mitternacht': 'Mitternacht',
        'polarstern': 'Polarstern',
        'rot': '(PRODUCT) Red Special Edition',
        'violett': 'Violett',
        'gelb': 'Gelb',
    }
    
    for i, p in enumerate(parts):
        if p.isdigit():
            if i > 0:
                model_base = parts[i-1]
                model_num = p
                suffix = '-'.join(parts[i+1:]) if i+1 < len(parts) else ''
                
                model = model_base + model_num
                if 'pro' in suffix:
                    if 'max' in suffix:
                        model += 'promax'
                    else:
                        model += 'pro'
                elif 'max' in suffix:
                    model += 'max'
                elif 'mini' in suffix:
                    model += 'mini'
                elif 'plus' in suffix:
                    model += 'plus'
                elif 'air' in suffix:
                    model += 'air'
                
                remaining = parts[i+1:] if i+1 < len(parts) else []
                for part in remaining:
                    if 'gb' in part.lower():
                        gb = part.upper()
                        break
                    elif 'tb' in part.lower():
                        gb = part.upper()
                        break
                
                for part in remaining:
                    part_lower = part.lower()
                    for color_key, color_value in color_map.items():
                        if color_key in part_lower:
                            color = color_value
                            break
                    if color:
                        break
            
            break
    
    return brand, model, gb, color


def get_vk_url(brand, model):
    return f"{VERKAUFEN_BASE}/handy-verkaufen/{brand}/{model}/"


def click_variation(driver, gb, color):
    try:
        human_pause()
        
        all_btns = driver.find_elements(By.CSS_SELECTOR, "button.configuration-option")
        
        gb_btn = None
        color_btn = None
        
        for btn in all_btns:
            btn_text = btn.text.strip()
            
            if gb:
                gb_clean = gb.replace('GB', '').replace('TB', '').strip()
                if gb_clean.isdigit():
                    num = int(gb_clean)
                    if num >= 32 and f'{num}' in btn_text:
                        gb_btn = btn
            
            if color:
                btn_lower = btn_text.lower()
                color_lower = color.lower()
                if color_lower in btn_lower or btn_lower in color_lower:
                    color_btn = btn
        
        if gb_btn:
            driver.execute_script("arguments[0].click();", gb_btn)
            human_pause()
        
        if color_btn:
            driver.execute_script("arguments[0].click();", color_btn)
            human_pause()
        
        page = driver.page_source
        match = re.search(r'Ankaufspreis f.r Neuware\s*([\d.,]+)', page)
        if match:
            preis = float(match.group(1).replace(',', '.'))
            return preis if preis > 10 else 0.0
        
        return 0.0
        
    except Exception as e:
        return 0.0


def main():
    print("=== VK Preis-Crawler v5.0 - VOLLSTAENDIG ===")
    
    df = pd.read_excel(INPUT_FILE)
    print(f"Zeilen: {len(df)}")
    
    # Alle Zeilen
    # df = df.head(3)  # Test
    
    options = Options()
    options.add_argument("--start-maximized")
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    
    all_results = []
    
    for idx, row in df.iterrows():
        name = row['Name']
        url_scrape = str(row['url scrape'])
        sku = row['sku']
        
        print(f"[{idx+1}/{len(df)}] {name}")
        
        brand, model, gb, color = extract_all_from_url(url_scrape)
        
        if not brand or not model:
            print(f"    FEHLER: Modell nicht erkannt")
            continue
        
        vk_link = get_vk_url(brand, model)
        
        driver.get(vk_link)
        human_pause()
        
        preis = click_variation(driver, gb, color)
        
        if preis > 0:
            preis_mindert = round(preis * 0.9, 2)
            variation = f"{color} {gb}" if color and gb else gb or color
            print(f"    Preis: {preis_mindert} EUR [{variation}]")
            
            all_results.append({
                "VK LINK": vk_link,
                "SKU": sku,
                "Preis (-10%)": preis_mindert,
                "Variation": variation
            })
        else:
            print(f"    FEHLER: Preis nicht gefunden")
            all_results.append({
                "VK LINK": vk_link,
                "SKU": sku,
                "Preis (-10%)": 0,
                "Variation": "FEHLER"
            })
        
        # Laengere Pause alle 10 Produkte
        if (idx + 1) % 10 == 0:
            print(f"    [Pause 10 Sekunden...]")
            time.sleep(10)
            
            # Zwischenspeichern
            temp_df = pd.DataFrame(all_results)
            temp_df.to_excel(OUTPUT_FILE, index=False)
            print(f"    [Zwischengespeichert: {len(all_results)}]")
        
        time.sleep(random.uniform(3, 7))
    
    if all_results:
        result_df = pd.DataFrame(all_results)
        result_df.to_excel(OUTPUT_FILE, index=False)
        print(f"\nFERTIG! {len(all_results)} Ergebnisse: {OUTPUT_FILE}")
    
    driver.quit()


if __name__ == "__main__":
    main()