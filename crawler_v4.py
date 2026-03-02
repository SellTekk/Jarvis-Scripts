"""
Verkaufen.de Preis-Crawler v4.0 - Mit Variationen
Langsam + menschliches Verhalten + alle Farben/Speicher

Output:
- A: VK LINK
- B: SKU
- C: Preis (10% abgezogen)
- D: Variation (Farbe + GB)
"""

import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import re

INPUT_FILE = "F:/crawlerv5/RELEASE.xlsx"
OUTPUT_FILE = "F:/crawlerv5/RELEASE_ergebnis.xlsx"
VERKAUFEN_BASE = "https://www.verkaufen.de"

# Langsame, menschliche Pausen
MIN_PAUSE = 2
MAX_PAUSE = 5


def human_pause():
    """Menschliche Pause zwischen Aktionen"""
    time.sleep(random.uniform(MIN_PAUSE, MAX_PAUSE))


def extract_brand_model(url):
    """Extrahiert Marke und Modell aus handyverkauf.net URL"""
    match = re.search(r'net/([a-z0-9-]+)_h_', url)
    if not match:
        return None, None
    
    name = match.group(1)
    parts = name.split('-')
    brand = parts[0]
    
    for i, p in enumerate(parts):
        if p.isdigit():
            model_base = parts[i-1] if i > 0 else ''
            model_num = p
            suffix = '-'.join(parts[i+1:]) if i+1 < len(parts) else ''
            
            model = model_base + model_num
            if 'pro' in suffix and 'max' in suffix:
                model += 'promax'
            elif 'pro' in suffix:
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
    else:
        model = '-'.join(parts[1:])
    
    return brand, model


def get_vk_url(brand, model):
    return f"{VERKAUFEN_BASE}/handy-verkaufen/{brand}/{model}/"


def get_preis(driver):
    """Findet den Neuware-Preis"""
    try:
        page = driver.page_source
        match = re.search(r'Ankaufspreis f.r Neuware\s*([\d.,]+)', page)
        if match:
            preis = float(match.group(1).replace(',', '.'))
            return preis if preis > 10 else 0.0
        return 0.0
    except:
        return 0.0


def click_variationen(driver, wait):
    """Klickt alle Variationen durch und sammelt Preise"""
    ergebnisse = []
    
    try:
        # Warten bis Seite geladen
        human_pause()
        
        # Speicher-Optionen finden
        try:
            storage_btns = driver.find_elements(By.CSS_SELECTOR, 
                "button.configuration-option, div.storage-options button, heading + div button")
            # Nur die mit GB drin
            storage_btns = [b for b in storage_btns if 'GB' in b.text or 'TB' in b.text]
        except:
            storage_btns = []
        
        # Farben finden
        try:
            color_btns = driver.find_elements(By.CSS_SELECTOR, 
                "button.configuration-option, div.color-options button")
            color_btns = [b for b in color_btns if b.text.strip()]
        except:
            color_btns = []
        
        # Default-Werte wenn keine Buttons gefunden
        if not storage_btns:
            storage_btns = [None]  # Default
        if not color_btns:
            color_btns = [None]  # Default
        
        print(f"    Speicher-Optionen: {len(storage_btns)}, Farben: {len(color_btns)}")
        
        # Jede Kombination durchgehen
        for s_idx, storage_btn in enumerate(storage_btns[:4]):  # Max 4 Speicher
            # Speicher klicken
            if storage_btn:
                try:
                    driver.execute_script("arguments[0].click();", storage_btn)
                    human_pause()
                except:
                    pass
            
            storage_text = storage_btn.text.strip() if storage_btn else "128 GB"
            
            for c_idx, color_btn in enumerate(color_btns[:6]):  # Max 6 Farben
                # Farbe klicken
                if color_btn:
                    try:
                        driver.execute_script("arguments[0].click();", color_btn)
                        human_pause()
                    except:
                        pass
                
                color_text = color_btn.text.strip() if color_btn else "Standard"
                
                # Preis holen
                preis = get_preis(driver)
                
                if preis > 0:
                    variation = f"{color_text} {storage_text}"
                    preis_mindert = round(preis * 0.9, 2)
                    ergebnisse.append({
                        "Preis": preis_mindert,
                        "Variation": variation
                    })
                    print(f"      {variation}: {preis} EUR -> {preis_mindert} EUR")
                
                # Zufällige längere Pause ab und zu
                if random.random() < 0.3:
                    time.sleep(random.uniform(3, 6))
        
    except Exception as e:
        print(f"    Fehler bei Variationen: {e}")
    
    return ergebnisse


def main():
    print("=== VK Preis-Crawler v4.0 ===")
    print("Langsam + Variationen + Menschlich")
    
    df = pd.read_excel(INPUT_FILE)
    print(f"Zeilen: {len(df)}")
    
    # Nur Test mit erster Zeile
    df = df.head(1)
    
    # Browser
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    
    all_results = []
    
    for idx, row in df.iterrows():
        name = row['Name']
        url_scrape = str(row['url scrape'])
        sku = row['sku']
        
        print(f"\n[{idx+1}] {name}")
        
        brand, model = extract_brand_model(url_scrape)
        if not brand or not model:
            print(f"  FEHLER: Modell nicht erkannt")
            continue
        
        vk_link = get_vk_url(brand, model)
        print(f"  URL: {vk_link}")
        
        # Seite öffnen
        driver.get(vk_link)
        human_pause()
        
        # Variationen durchklicken
        variationen = click_variationen(driver, wait)
        
        # Ergebnisse speichern
        for v in variationen:
            all_results.append({
                "VK LINK": vk_link,
                "SKU": sku,
                "Preis (-10%)": v["Preis"],
                "Variation": v["Variation"]
            })
        
        # Längere Pause zwischen Produkten
        time.sleep(random.uniform(5, 10))
    
    # Speichern
    if all_results:
        result_df = pd.DataFrame(all_results)
        result_df.to_excel(OUTPUT_FILE, index=False)
        print(f"\nFertig! {len(all_results)} Ergebnisse gespeichert: {OUTPUT_FILE}")
    
    driver.quit()


if __name__ == "__main__":
    main()