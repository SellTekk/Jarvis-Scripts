"""
Verkaufen.de Preis-Crawler v5.0 - Mit korrekter Zuordnung

Extrahiert Farbe + GB aus handyverkauf.net URL und klickt nur die passende Kombination.

Output:
- A: VK LINK
- B: SKU
- C: Preis (10% abgezogen)
- D: Variation (Farbe + GB)
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

# Proxy - auskommentieren wenn nicht benoetigt
PROXY = "localhost:9999"  # proxy-chain Server

# Browser IMMER SICHTBAR (wie Idealo-Crawler)
HEADLESS = False

# ===== DEBUGGING STUFE 1 =====
DEBUG = True
LOG_FILE = "C:/Users/no/.openclaw/workspace-verkaufen-decrawler/debug_log.txt"
MAX_RETRIES = 3
IP_CHECK_EVERY = 10  # Check IP alle 10 Produkte
MAX_CONSECUTIVE_ERRORS = 3  # Browser-Neustart nach 3 Fehlern

# Stats
stats = {
    "total": 0,
    "success": 0,
    "errors": 0,
    "retries": 0,
    "browser_restarts": 0
}

def log(msg, level="INFO"):
    """Schreibt Debug-Nachrichten in Datei und Console"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] [{level}] {msg}"
    print(log_msg)
    if DEBUG:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_msg + "\n")
        except:
            pass

def log_error(sku, url, error_type, action):
    """Loggt Fehler für spätere Analyse"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] ERROR | SKU:{sku} | URL:{url} | Type:{error_type} | Action:{action}"
    try:
        with open("C:/Users/no/.openclaw/workspace-verkaufen-decrawler/error_log.csv", "a", encoding="utf-8") as f:
            f.write(f"{timestamp},{sku},{url},{error_type},{action}\n")
    except:
        pass


def check_ip(driver):
    """Prueft aktuelle IP und erkennt Blockierung"""
    try:
        log("[*] Pruefe IP...")
        driver.get("https://whoer.net/")
        time.sleep(3)
        
        page = driver.page_source
        
        # IP finden
        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', page)
        if match:
            ip = match.group(1)
            log(f"[+] Aktuelle IP: {ip}")
            return ip
        
        # Cloudflare Check
        if "Just a moment" in page or "Cloudflare" in page:
            log("[!] Cloudflare Challenge erkannt!", "WARN")
            return None
            
        log("[!] IP nicht gefunden", "WARN")
        return None
    except Exception as e:
        log(f"[!] IP-Check Fehler: {e}", "ERROR")
        return None


def detect_blocking(page_source):
    """Erkennt verschiedene Blockierungs-Typen"""
    errors = []
    
    if not page_source:
        errors.append("EMPTY_PAGE")
    
    if "Just a moment" in page_source or "cloudflare" in page_source.lower():
        errors.append("CLOUDFLARE")
    
    if "403" in page_source or "Forbidden" in page_source:
        errors.append("HTTP_403")
    
    if "429" in page_source or "Too Many Requests" in page_source:
        errors.append("HTTP_429")
    
    if "Unusual traffic" in page_source or "unusual traffic" in page_source.lower():
        errors.append("UNUSUAL_TRAFFIC")
    
    if "blocked" in page_source.lower() or "sperre" in page_source.lower():
        errors.append("BLOCKED")
    
    return errors


def create_driver_fresh():
    """Erstellt neuen Browser - SICHTBAR wenn HEADLESS=False"""
    log(f"[*] Erstelle neuen Browser (HEADLESS={HEADLESS})...")
    options = Options()
    
    # Sichtbar oder headless je nach Einstellung
    if HEADLESS:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
    
    options.add_argument("--start-maximized")
    options.add_argument("--new-window")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--lang=de-DE")
    
    log(f"[*] Chrome-Optionen: HEADLESS={HEADLESS}")
    
    if PROXY:
        options.add_argument(f"--proxy-server={PROXY}")
        log(f"[*] Proxy: {PROXY}")
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    log("[+] Browser erstellt")
    return driver, wait


MIN_PAUSE = 2
MAX_PAUSE = 5


def human_pause():
    time.sleep(random.uniform(MIN_PAUSE, MAX_PAUSE))


def extract_all_from_url(url):
    """
    Extrahiert: Marke, Modell, GB, Farbe aus handyverkauf.net URL
    Bsp: https://www.handyverkauf.net/apple-iphone-14-128gb-blau_h_10788
    -> brand=apple, model=iphone14, gb=128gb, color=blau
    """
    match = re.search(r'net/([a-z0-9-]+)_h_', url)
    if not match:
        return None, None, None, None
    
    name = match.group(1)  # apple-iphone-14-128gb-blau
    parts = name.split('-')
    
    brand = parts[0]
    model = None
    gb = None
    color = None
    
    # Farben-Mapping
    color_map = {
        'blau': 'Blau',
        'mitternacht': 'Mitternacht',
        'polarstern': 'Polarstern',
        'rot': '(PRODUCT) Red Special Edition',
        'violett': 'Violett',
        'gelb': 'Gelb',
        'schwarz': 'Schwarz',
        'weiss': 'Weiss',
        'grau': 'Grau',
        'silber': 'Silber',
        'gold': 'Gold',
    }
    
    for i, p in enumerate(parts):
        if p.isdigit():
            # Modell
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
                
                # GB finden
                remaining = parts[i+1:] if i+1 < len(parts) else []
                for part in remaining:
                    if 'gb' in part.lower():
                        gb = part.upper()
                        break
                    elif 'tb' in part.lower():
                        gb = part.upper()
                        break
                
                # Farbe finden (letzter Teil)
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
    """Klickt nur die spezifische GB + Farbe Kombination"""
    try:
        human_pause()
        
        all_btns = driver.find_elements(By.CSS_SELECTOR, "button.configuration-option")
        
        gb_btn = None
        color_btn = None
        
        for btn in all_btns:
            btn_text = btn.text.strip()
            
            # GB-Button (nur Storage >= 32GB)
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
                if color_lower in btn_lower or btn_lower in color_lower:
                    color_btn = btn
        
        print(f"      Suche GB={gb}, Farbe={color}")
        
        if gb_btn:
            print(f"      Klicke GB: {gb_btn.text}")
            driver.execute_script("arguments[0].click();", gb_btn)
            human_pause()
        
        if color_btn:
            print(f"      Klicke Farbe: {color_btn.text}")
            driver.execute_script("arguments[0].click();", color_btn)
            human_pause()
        
        # Preis
        page = driver.page_source
        match = re.search(r'Ankaufspreis f.r Neuware\s*([\d.,]+)', page)
        if match:
            preis = float(match.group(1).replace(',', '.'))
            return preis if preis > 10 else 0.0
        
        return 0.0
        
    except Exception as e:
        print(f"      Fehler: {e}")
        return 0.0


def main():
    print("=== VK Preis-Crawler v5.0 - DEBUG STUFE 1 ===")
    
    # Loesche alte Logs
    try:
        open("C:/Users/no/.openclaw/workspace-verkaufen-decrawler/error_log.csv", "w").close()
    except:
        pass
    
    df = pd.read_excel(INPUT_FILE)
    print(f"Zeilen: {len(df)}")
    
    # ALLE 837 Produkte
    # df = df.head(50)  # Test-Version
    print(f"ALLE {len(df)} Produkte")
    
    # Erstelle Browser
    driver, wait = create_driver_fresh()
    
    all_results = []
    consecutive_errors = 0
    
    # Initialer IP-Check
    check_ip(driver)
    
    for idx, row in df.iterrows():
        stats["total"] += 1
        name = row['Name']
        url_scrape = str(row['url scrape'])
        sku = row['sku']
        
        print(f"\n[{idx+1}/{len(df)}] {name}")
        
        # IP-Check alle N Produkte
        if (idx + 1) % IP_CHECK_EVERY == 0:
            check_ip(driver)
        
        # Retry-Logik
        preis = 0
        success = False
        
        for attempt in range(MAX_RETRIES):
            try:
                brand, model, gb, color = extract_all_from_url(url_scrape)
                
                if not brand or not model:
                    log(f"Modell nicht erkannt: {url_scrape}", "ERROR")
                    log_error(sku, url_scrape, "NO_MODEL", "skip")
                    break
                
                vk_link = get_vk_url(brand, model)
                
                driver.get(vk_link)
                human_pause()
                
                # Blockierung erkennen
                page = driver.page_source
                blocking = detect_blocking(page)
                
                if blocking:
                    log(f"Blockierung erkannt: {blocking}", "WARN")
                    log_error(sku, vk_link, str(blocking), "retry")
                    
                    if attempt < MAX_RETRIES - 1:
                        log(f"Retry {attempt+2}/{MAX_RETRIES}...", "WARN")
                        time.sleep(10)  # Laenger warten
                        continue
                    else:
                        break
                
                preis = click_variation(driver, gb, color)
                
                if preis > 0:
                    success = True
                    break
                else:
                    log("Preis nicht gefunden", "WARN")
                    if attempt < MAX_RETRIES - 1:
                        stats["retries"] += 1
                        log(f"Retry {attempt+2}/{MAX_RETRIES}...", "WARN")
                        
            except Exception as e:
                log(f"Fehler: {e}", "ERROR")
                log_error(sku, url_scrape, str(type(e).__name__), "retry")
                
                if attempt < MAX_RETRIES - 1:
                    stats["retries"] += 1
                    time.sleep(5)
        
        # Ergebnis verarbeiten
        if success and preis > 0:
            preis_mindert = round(preis * 0.9, 2)
            variation = f"{color} {gb}" if color and gb else gb or color
            print(f"    Preis: {preis_mindert} EUR [{variation}]")
            
            all_results.append({
                "VK LINK": vk_link,
                "SKU": sku,
                "Preis (-10%)": preis_mindert,
                "Variation": variation
            })
            
            stats["success"] += 1
            consecutive_errors = 0
        else:
            print(f"    FEHLER: Preis nicht gefunden nach {MAX_RETRIES} Versuchen")
            all_results.append({
                "VK LINK": vk_link if 'vk_link' in dir() else "",
                "SKU": sku,
                "Preis (-10%)": 0,
                "Variation": "FEHLER"
            })
            log_error(sku, url_scrape, "MAX_RETRIES", "skipped")
            stats["errors"] += 1
            consecutive_errors += 1
        
        # Browser-Neustart bei zu vielen Fehlern
        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            log("Zu viele Fehler - Browser wird neugestartet...", "WARN")
            try:
                driver.quit()
            except:
                pass
            time.sleep(5)
            driver, wait = create_driver_fresh()
            check_ip(driver)
            consecutive_errors = 0
            stats["browser_restarts"] += 1
        
        # Zwischenspeichern alle 10
        if (idx + 1) % 10 == 0:
            temp_df = pd.DataFrame(all_results)
            temp_df.to_excel(OUTPUT_FILE, index=False)
            log(f"Zwischengespeichert: {len(all_results)} Ergebnisse")
    
    # Ende
    if all_results:
        result_df = pd.DataFrame(all_results)
        result_df.to_excel(OUTPUT_FILE, index=False)
    
    # Statistik
    log("=== STATISTIK ===")
    log(f"Total: {stats['total']}")
    log(f"Erfolgreich: {stats['success']}")
    log(f"Fehler: {stats['errors']}")
    log(f"Retries: {stats['retries']}")
    log(f"Browser-Neustarts: {stats['browser_restarts']}")
    
    driver.quit()
    print("\nFertig!")


if __name__ == "__main__":
    main()