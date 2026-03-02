"""
Verkaufen.de Preis-Crawler v6.0 - Komplettloesung

1. Liest handyverkauf URLs aus Excel
2. Konvertiert zu verkaufen.de URLs (in Excel)
3. Fuer jedes Modell: alle Speicher-Varianten crawlen
4. Jede SKU erhaelt die korrekte Preiskombination
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


def convert_url_to_vk(url):
    """Konvertiert handyverkauf.net zu verkaufen.de URL"""
    match = re.search(r'net/([a-z0-9-]+)_h_', url)
    if not match:
        return None
    
    name = match.group(1)
    parts = name.split('-')
    
    brand = parts[0]
    model = None
    
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
            break
    
    if not brand or not model:
        return None
    
    return f"{VERKAUFEN_BASE}/handy-verkaufen/{brand}/{model}/"


def extract_gb_from_url(url):
    """Extrahiert GB aus handyverkauf URL"""
    match = re.search(r'net/([a-z0-9-]+)_h_', url)
    if not match:
        return None
    
    name = match.group(1)
    parts = name.split('-')
    
    for part in parts:
        part_lower = part.lower()
        if 'gb' in part_lower:
            return part.upper()
        elif 'tb' in part_lower:
            return part.upper()
    return None


def get_all_storage_prices(driver):
    """Crawlt alle Speicher-Preise fuer ein Modell"""
    prices = {}
    
    try:
        human_pause()
        
        all_btns = driver.find_elements(By.CSS_SELECTOR, "button.configuration-option")
        
        storage_btns = []
        for btn in all_btns:
            btn_text = btn.text.strip()
            if 'GB' in btn_text or 'TB' in btn_text:
                num_str = btn_text.replace('GB', '').replace('TB', '').strip()
                if num_str.isdigit():
                    if int(num_str) >= 32:
                        storage_btns.append((btn, btn_text))
        
        for btn, btn_text in storage_btns[:4]:
            try:
                driver.execute_script("arguments[0].click();", btn)
                human_pause()
                
                page = driver.page_source
                match = re.search(r'Ankaufspreis f.r Neuware\s*([\d.,]+)', page)
                if match:
                    preis = float(match.group(1).replace(',', '.'))
                    if preis > 10:
                        storage = btn_text.replace(' ', '')
                        prices[storage] = preis
                        print(f"      {storage}: {preis} EUR")
            except:
                pass
        
    except Exception as e:
        print(f"      Fehler: {e}")
    
    return prices


def main():
    print("=== VK Preis-Crawler v6.0 ===")
    
    df = pd.read_excel(INPUT_FILE)
    print(f"Zeilen: {len(df)}")
    
    # URLs konvertieren
    print("\n1. Konvertiere URLs...")
    vk_links = []
    for idx, row in df.iterrows():
        url = str(row['url scrape'])
        vk_link = convert_url_to_vk(url)
        vk_links.append(vk_link)
    
    df['VK LINK'] = vk_links
    
    # Einmalige Modelle finden
    unique_vk = df['VK LINK'].dropna().unique().tolist()
    print(f"Einmalige Modelle: {len(unique_vk)}")
    
    # Browser
    options = Options()
    options.add_argument("--start-maximized")
    
    driver = webdriver.Chrome(options=options)
    
    # Test: erste 2 Modelle
    test_models = unique_vk[:2]
    
    results = []
    
    for vk_link in test_models:
        print(f"\nCrawle: {vk_link}")
        
        driver.get(vk_link)
        human_pause()
        
        # Alle Preise holen
        all_prices = get_all_storage_prices(driver)
        
        # Fuer jede Zeile mit diesem VK LINK
        for idx, row in df.iterrows():
            if row['VK LINK'] == vk_link:
                sku = row['sku']
                original_url = str(row['url scrape'])
                
                # GB aus Original-URL extrahieren
                gb = extract_gb_from_url(original_url)
                
                # Preis finden
                preis = 0
                preis_text = ""
                
                if gb and all_prices:
                    # Normalisieren
                    gb_norm = gb.replace('GB', '').strip()
                    for storage_key, storage_preis in all_prices.items():
                        if gb_norm in storage_key:
                            preis = round(storage_preis * 0.9, 2)
                            preis_text = storage_key
                            break
                
                results.append({
                    "VK LINK": vk_link,
                    "SKU": sku,
                    "Preis (-10%)": preis,
                    "Variation": preis_text
                })
                
                print(f"   SKU {sku}: {preis} EUR [{preis_text}]")
                
                # Pause
                time.sleep(random.uniform(3, 6))
    
    # Speichern
    if results:
        result_df = pd.DataFrame(results)
        result_df.to_excel(OUTPUT_FILE, index=False)
        print(f"\nFertig! {len(results)} Ergebnisse: {OUTPUT_FILE}")
    
    driver.quit()


if __name__ == "__main__":
    main()