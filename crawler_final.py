"""
Verkaufen.de Preis-Crawler v3.0
Basierend auf OpenClaw Browser Analyse

Workflow:
1. Liest RELEASE.xlsx (handyverkauf.net URLs)
2. Wandelt URL in verkaufen.de URL um
3. Scraped Neuware-Preis von der Seite
4. Zieht 10% ab
5. Speichert in RELEASE_ergebnis.xlsx

Output-Spalten:
- A: VK LINK (verkaufen.de)
- B: SKU
- C: Preis (10% abgezogen)
"""

import pandas as pd
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import sys

# Konfiguration
INPUT_FILE = "F:/crawlerv5/RELEASE.xlsx"
OUTPUT_FILE = "F:/crawlerv5/RELEASE_ergebnis.xlsx"
VERKAUFEN_BASE = "https://www.verkaufen.de"
PAUSE = 3


def extract_brand_model(url):
    """
    Extrahiert Marke und Modell aus handyverkauf.net URL
    Bsp: https://www.handyverkauf.net/apple-iphone-14-128gb-blau_h_10788
    -> brand: apple, model: iphone14
    """
    match = re.search(r'net/([a-z0-9-]+)_h_', url)
    if not match:
        return None, None
    
    name = match.group(1)
    parts = name.split('-')
    brand = parts[0]
    
    # Modell finden
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
    """Erstellt die verkaufen.de URL"""
    return f"{VERKAUFEN_BASE}/handy-verkaufen/{brand}/{model}/"


def get_neuware_preis(driver):
    """
    Extrahiert den Neuware-Preis von der aktuellen Seite
    Sucht nach: 'Ankaufspreis für Neuware XXX,XX EUR'
    """
    try:
        page_text = driver.page_source
        
        # Preis finden - verschiedene Pattern
        patterns = [
            r'Ankaufspreis f.r Neuware\s*([\d.,]+)\s*EUR',
            r'Ankaufspreis f.r Neuware\s*([\d.,]+)',
            r'Neuware\s*([\d.,]+)\s*EUR',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                preis_str = match.group(1).replace(',', '.')
                try:
                    preis = float(preis_str)
                    if preis > 10:  # Plausibilitätsprüfung
                        return preis
                except:
                    pass
        
        return 0.0
    except Exception as e:
        print(f"Preis-Fehler: {e}")
        return 0.0


def crawl_preis(vk_url, driver):
    """Crawlt den Preis von einer verkaufen.de Seite"""
    try:
        driver.get(vk_url)
        time.sleep(PAUSE)
        
        preis = get_neuware_preis(driver)
        return preis
    except Exception as e:
        print(f"Crawl-Fehler: {e}")
        return 0.0


def main():
    """Hauptfunktion"""
    print("=== Verkaufen.de Preis-Crawler v3.0 ===")
    print(f"Input: {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print()
    
    # Excel einlesen
    print("Lese RELEASE.xlsx...")
    df = pd.read_excel(INPUT_FILE)
    print(f"Gefunden: {len(df)} Zeilen")
    
    # Für Test: nur erste 3 Zeilen
    # df = df.head(3)
    
    # Browser starten
    print("\nStarte Browser...")
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    
    # Ergebnisse sammeln
    results = []
    
    for idx, row in df.iterrows():
        name = row['Name']
        url_scrape = str(row['url scrape'])
        sku = row['sku']
        
        print(f"\n[{idx+1}/{len(df)}] {name}")
        
        # Marke und Modell extrahieren
        brand, model = extract_brand_model(url_scrape)
        
        if not brand or not model:
            print(f"  FEHLER: Konnte Modell nicht extrahieren aus: {url_scrape}")
            vk_link = ""
            preis = 0.0
        else:
            # VK URL erstellen
            vk_link = get_vk_url(brand, model)
            print(f"  URL: {vk_link}")
            
            # Preis crawlen
            preis = crawl_preis(vk_link, driver)
            
            if preis > 0:
                preis_mindert = round(preis * 0.9, 2)
                print(f"  Preis: {preis} EUR -> Nach 10% Abzug: {preis_mindert} EUR")
            else:
                preis_mindert = 0.0
                print(f"  FEHLER: Konnte Preis nicht finden")
        
        # Ergebnis speichern
        results.append({
            "VK LINK": vk_link,
            "SKU": sku,
            "Preis (-10%)": preis_mindert
        })
        
        # Alle 10 Zeilen zwischenspeichern
        if (idx + 1) % 10 == 0:
            temp_df = pd.DataFrame(results)
            temp_df.to_excel(OUTPUT_FILE, index=False)
            print(f"  [Zwischengespeichert: {OUTPUT_FILE}]")
    
    # Final speichern
    print("\nSpeichere Ergebnisse...")
    result_df = pd.DataFrame(results)
    result_df.to_excel(OUTPUT_FILE, index=False)
    print(f"Fertig! Gespeichert: {OUTPUT_FILE}")
    
    # Browser schließen
    driver.quit()
    print("\n=== CRAWL FERTIG ===")


if __name__ == "__main__":
    main()