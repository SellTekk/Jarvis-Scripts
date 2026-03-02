"""
Verkaufen.de Preis-Crawler v2.0 - Based on OpenClaw Browser analysis
"""

import pandas as pd
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

INPUT_FILE = "F:/crawlerv5/RELEASE.xlsx"
OUTPUT_FILE = "F:/crawlerv5/RELEASE_ergebnis.xlsx"
VERKAUFEN_BASE = "https://www.verkaufen.de"
PAUSE = 3

def extract_model_from_url(url):
    \"\"\"Extrahiert Marke und Modell aus handyverkauf.net URL.\"\"\"
    match = re.search(r'net/([a-z0-9-]+)_h_', url)
    if not match:
        return None, None
    
    name = match.group(1)
    parts = name.split('-')
    brand = parts[0]
    
    # Build model
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
    \"\"\"Erstellt die verkaufen.de URL.\"\"\"
    return f"{VERKAUFEN_BASE}/handy-verkaufen/{brand}/{model}/"

def get_neuware_price(driver):
    \"\"\"Extrahiert den Neuware-Preis von der aktuellen Seite.\"\"\"
    try:
        # Der Preis steht oben auf der Seite: "Ankaufspreis für Neuware XXX,XX EUR"
        page_text = driver.page_source
        
        # Suche nach dem Preis
        match = re.search(r'Ankaufspreis f.r Neuware\s*([\d.,]+)\s*€', page_text, re.IGNORECASE)
        if match:
            preis = float(match.group(1).replace(',', '.'))
            return preis
        
        # Alternative: suche nach "Neuware" und nimm den ersten Preis daneben
        # Oder suche nach dem höchsten Preis in der Liste
        return 0.0
    except Exception as e:
        print(f"  Preis-Fehler: {e}")
        return 0.0

# Test
print("=== TEST: URL Extraction ===")
test_urls = [
    'https://www.handyverkauf.net/apple-iphone-14-128gb-blau_h_10788',
]
for url in test_urls:
    brand, model = extract_model_from_url(url)
    vk_url = get_vk_url(brand, model)
    print(f"Original: {url}")
    print(f"  -> Brand: {brand}, Model: {model}")
    print(f"  -> VK URL: {vk_url}")

print("\n=== TEST: Browser & Preis ===")
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

# Test mit iPhone 14
vk_url = "https://www.verkaufen.de/handy-verkaufen/apple/iphone14/"
print(f"Oeffne: {vk_url}")
driver.get(vk_url)
time.sleep(PAUSE)

preis = get_neuware_price(driver)
print(f"Neuware Preis: {preis} EUR")
print(f"Mit 10% Abzug: {preis * 0.9:.2f} EUR")

driver.quit()
print("\n=== FERTIG ===")
