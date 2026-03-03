"""
VK Preis-Crawler - NUR Preise abrufen
Liest VK LINKs aus Excel und holt Preise (keine Link-Analyse mehr)
"""
import pandas as pd
import time
import random
import re
import os
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === ROBUSTNESS ===
SAVE_EVERY = 20
MAX_PRODUCTS_BEFORE_RESTART = 30

# === Orphan Chrome killen ===
def kill_orphans():
    subprocess.run(["taskkill", "/F", "/IM", "chromedriver.exe", "/T"], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], 
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# === Browser erstellen ===
def create_browser():
    kill_orphans()
    time.sleep(0.5)
    
    options = Options()
    # Stabil
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Lean
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disk-cache-size=1")
    prefs = {
        "profile.managed_default_content_settings.images": 2,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    if PROXY:
        options.add_argument(f"--proxy-server={PROXY}")
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver, WebDriverWait(driver, 15)

# === KONFIGURATION ===
# Wähle: "handy" oder "tablet"
PRODUKT_TYP = "handy"

if PRODUKT_TYP == "handy":
    INPUT_FILE = "F:/crawlerv5/RELEASE_handy_ergebnis.xlsx"
    OUTPUT_FILE = "F:/crawlerv5/RELEASE_handy_ergebnis.xlsx"
elif PRODUKT_TYP == "tablet":
    INPUT_FILE = "F:/crawlerv5/RELEASE_tablet_ergebnis.xlsx"
    OUTPUT_FILE = "F:/crawlerv5/RELEASE_tablet_ergebnis.xlsx"

PROXY = None  # Kein Proxy für Stabilität! # "localhost:9999"
VERKAUFEN_BASE = "https://www.verkaufen.de"

MIN_PAUSE = 2
MAX_PAUSE = 5

def human_pause():
    time.sleep(random.uniform(MIN_PAUSE, MAX_PAUSE))

def click_variation(driver, gb, color):
    """Klickt nur die spezifische GB + Farbe Kombination"""
    try:
        human_pause()
        all_btns = driver.find_elements(By.CSS_SELECTOR, "button.configuration-option")
        
        gb_btn = None
        color_btn = None
        
        # Farb-Alias
        color_aliases = {
            'schwarz': ['schwarz', 'black', 'phantom black', 'midnight', 'onyx'],
            'weiss': ['weiss', 'white', 'pearl', 'glacier', 'polar'],
            'blau': ['blau', 'blue', 'ocean', 'sky', 'navy', 'pacific', 'azure'],
            'grau': ['grau', 'gray', 'grey', 'graphite', 'titanium', 'space grey'],
            'silber': ['silber', 'silver', 'platinum'],
            'gold': ['gold', 'golden', 'champagne'],
            'rot': ['rot', 'red', '(product) red', 'coral', 'burgundy', 'bordeaux'],
            'gruen': ['gruen', 'green', 'mint', 'olive', 'forest', 'emerald'],
            'violett': ['violett', 'purple', 'violet', 'lavender', 'aurora'],
            'gelb': ['gelb', 'yellow'],
            'rose': ['rose', 'pink', 'rose gold', 'blush'],
            'lime': ['lime', 'lime green'],
            'orange': ['orange', 'apricot', 'sunset'],
            'beige': ['beige', 'cream', 'ivory', 'pearl'],
            'braun': ['braun', 'brown', 'bronze', 'copper'],
            'cyan': ['cyan', 'turquoise', 'teal'],
        }
        
        for btn in all_btns:
            btn_text = btn.text.strip()
            
            # GB-Button
            if gb:
                gb_clean = gb.replace('GB', '').replace('TB', '').strip()
                if gb_clean.isdigit():
                    num = int(gb_clean)
                    if num >= 32 and f'{num}' in btn_text:
                        gb_btn = btn
            
            # Farbe-Button
            if color:
                btn_lower = btn_text.lower()
                color_lower = color.lower()
                
                target_aliases = None
                for main_color, aliases in color_aliases.items():
                    if color_lower in aliases:
                        target_aliases = aliases
                        break
                
                if target_aliases:
                    for alias in target_aliases:
                        if alias in btn_lower:
                            color_btn = btn
                            break
                else:
                    if color_lower in btn_lower or btn_lower in color_lower:
                        color_btn = btn
        
        print(f"      Suche GB={gb}, Farbe={color}")
        
        if gb_btn:
            print(f"      Klicke GB: {gb_btn.text}")
            driver.execute_script("arguments[0].click();", gb_btn)
            time.sleep(2)
        
        if color_btn:
            print(f"      Klicke Farbe: {color_btn.text}")
            driver.execute_script("arguments[0].click();", color_btn)
            time.sleep(3)
        
        time.sleep(2)
        
        page = driver.page_source
        
        # 404 check
        if "Seite nicht gefunden" in page or "existiert nicht" in page.lower():
            return -1
        
        # Kein Preis check
        if "kein einkaufspreis" in page.lower() or "kein ankaufspreis" in page.lower():
            return -2
        
        # Preis
        match = re.search(r'Ankaufspreis f.r Neuware\s*([\d.,]+)', page)
        if match:
            preis = float(match.group(1).replace(',', '.'))
            return preis if preis > 10 else 0.0
        
        return 0.0
        
    except Exception as e:
        print(f"      Fehler: {e}")
        return 0.0

def main():
    print("=== VK Preis-Crawler v6.0 (NUR PREISE) ===")
    
    # Lese VK LINKs aus Excel
    df = pd.read_excel(INPUT_FILE)
    print(f"Zeilen: {len(df)}")
    
    driver, wait = create_browser()
    print(f"[*] Browser gestartet")
    
    all_results = []
    processed_skus = set()
    products_processed = 0
    
    # Lade bestehende Ergebnisse - ABER immer NEU crawlen für frische Preise!
    # (also: NICHT überspringen)
                        "Variation": r["Variation"]
                    })
                    processed_skus.add(r["SKU"])
            print(f"[*] {len(processed_skus)} bereits verarbeitete SKUs mit Preis gefunden")
        except:
            pass
    
    for idx, row in df.iterrows():
        vk_link = row['VK LINK']
        sku = row['SKU']
        
        if sku in processed_skus:
            continue
        
        # Extrahiere GB und Farbe aus Variation
        variation = row.get('Variation', '')
        
        # Versuche GB und Farbe aus Variation zu extrahieren
        gb = None
        color = None
        
        if variation:
            # GB finden
            gb_match = re.search(r'(\d+)\s*GB', variation, re.I)
            if gb_match:
                gb = gb_match.group(1) + 'GB'
            
            # Farbe - alles andere
            color = variation
            if gb:
                color = color.replace(gb, '').strip()
        
        print(f"\n[{idx+1}] {variation}")
        
        preis = 0
        for retry in range(2):
            try:
                driver.get(vk_link)
                human_pause()
                
                preis = click_variation(driver, gb, color)
                
                if preis > 0:
                    break
                elif preis == -2:
                    break
                    
            except Exception as e:
                print(f"    FEHLER: {e}")
                time.sleep(5)
        
        if preis > 0:
            preis_mindert = round(preis * 0.9, 2)
            print(f"    Preis: {preis} EUR -> {preis_mindert} EUR")
            
            all_results.append({
                "VK LINK": vk_link,
                "SKU": sku,
                "Preis (-10%)": preis_mindert,
                "Variation": variation
            })
        else:
            print(f"    FEHLER: Preis nicht gefunden")
        
        # Speichern nur alle 20 Produkte
        if all_results and len(all_results) % SAVE_EVERY == 0:
            result_df = pd.DataFrame(all_results)
            result_df.to_excel(OUTPUT_FILE, index=False)
            print(f"    💾 Zwischenspeicher: {len(all_results)}")
        
        # Browser restart alle 30 Produkte
        products_processed += 1
        if products_processed >= MAX_PRODUCTS_BEFORE_RESTART:
            print(f"\n🔄 Browser-Neustart nach {products_processed} Produkten...")
            driver.quit()
            driver, wait = create_browser()
            products_processed = 0
        
        time.sleep(random.uniform(3, 6))
    
    # Finale Speicherung
    if all_results:
        result_df = pd.DataFrame(all_results)
        result_df.to_excel(OUTPUT_FILE, index=False)
    
    driver.quit()
    print("\n=== FERTIG ===")

if __name__ == "__main__":
    import os
    main()
