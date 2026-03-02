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
import os
import subprocess
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
        'rose': 'Rose',
        'gruen': 'Gruen',
        'space': 'Space Schwarz',
        'graphit': 'Graphit',
    }
    
    for i, p in enumerate(parts):
        # Auch Modelle mit Buchstaben erkennen (s22, a54, etc.)
        if p.isdigit() or (any(c.isalpha() for c in p) and any(c.isdigit() for c in p)):
            # Modell
            if i > 0:
                model_base = parts[i-1]
                model_num = p
                suffix = '-'.join(parts[i+1:]) if i+1 < len(parts) else ''
                
                model = model_base + model_num
                
                # Spezielle Modelle: flip, z, fold erkennen - mit Bindestrichen für URL!
                if model_base in ['flip', 'z'] or 'flip' in model_base:
                    model = 'galaxy-z-flip-' + model_num
                elif 'fold' in model_base:
                    model = 'galaxy-z-fold-' + model_num
                elif model_base in ['ultra']:
                    # ultra ist schon im model_base (z.B. von "s22ultra"), nichts tun
                    pass
                elif 'ultra' in suffix:
                    model += 'ultra'
                elif 'pro' in suffix:
                    if 'max' in suffix:
                        model += 'promax'
                    else:
                        model += 'pro'
                elif 'max' in suffix:
                    model += 'max'
                elif 'plus' in suffix:
                    model += '+'  # "plus" wird zu "+"!
                elif 'mini' in suffix:
                    model += 'mini'
                elif 'flip' in suffix:
                    model = 'galaxyzflip' + model_num  # flip -> galaxyzflip!
                elif 'plus' in suffix:
                    model += 'plus'
                elif 'air' in suffix:
                    model += 'air'
                
                # GB und Farbe finden (alle in einem Durchlauf!)
                remaining = parts[i+1:] if i+1 < len(parts) else []
                
                # ALLE Modell-Suffixes aus remaining entfernen!
                # Diese Wörter sind Teil des Modellnamens, keine Farben!
                model_suffix = ['pro', 'max', 'mini', 'plus', 'air', 'ultra', 'promax', 'flip', 'z', 'plus']
                remaining = [p for p in remaining if p.lower() not in model_suffix]
                
                for part in remaining:
                    part_lower = part.lower()
                    
                    # GB finden (aber NICHT abbrechen!)
                    if not gb:
                        if 'gb' in part_lower:
                            gb = part.upper()
                        elif 'tb' in part_lower:
                            gb = part.upper()
                    
                    # Farbe finden - erst aus Map, sonst aus URL (dynamisch)
                    # WICHTIG: Nur Farbe setzen wenn es KEIN GB/TB ist!
                    if not color and 'gb' not in part_lower and 'tb' not in part_lower:
                        # Versuche erst die color_map
                        for color_key, color_value in color_map.items():
                            if color_key in part_lower:
                                color = color_value
                                break
                        # Wenn nicht in Map: nimm den Teil direkt (z.B. "graphit" -> "Graphit")
                        if not color and not part.isdigit():
                            color = part.capitalize()
            
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
            
            # Farbe-Button - mit dynamischer Erkennung
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
    print("=== VK Preis-Crawler v5.0 ===")
    
    df = pd.read_excel(INPUT_FILE)
    print(f"Zeilen: {len(df)}")
    
    # Alle 837 Zeilen verarbeiten
    # df = df.head(10)  # Debug: nur erste 10
    
    options = Options()
    options.add_argument("--start-maximized")
    
    # Proxy verwenden
    if PROXY:
        options.add_argument(f"--proxy-server={PROXY}")
        print(f"[*] Proxy: {PROXY}")
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    
    # Bestehende Ergebnisse laden (falls vorhanden)
    all_results = []
    processed_skus = set()
    if os.path.exists(OUTPUT_FILE):
        try:
            existing_df = pd.read_excel(OUTPUT_FILE)
            for _, r in existing_df.iterrows():
                all_results.append({
                    "VK LINK": r["VK LINK"],
                    "SKU": r["SKU"],
                    "Preis (-10%)": r["Preis (-10%)"],
                    "Variation": r["Variation"]
                })
                processed_skus.add(r["SKU"])
            print(f"[*] {len(processed_skus)} bereits verarbeitete SKUs gefunden")
        except:
            pass
    
    products_processed = 0
    
    for idx, row in df.iterrows():
        sku = row['sku']
        
        # Überspringe bereits verarbeitete
        if sku in processed_skus:
            continue
        products_processed += 1
        
        # Kein automatischer Browser-Neustart - nur bei Fehlern (Retry)
        
        name = row['Name']
        url_scrape = str(row['url scrape'])
        
        print(f"\n[{idx+1}] {name}")
        
        # Retry-Logik: Produkt bis zu 3x versuchen
        max_retries = 3
        preis = 0
        
        for retry in range(max_retries):
            try:
                brand, model, gb, color = extract_all_from_url(url_scrape)
                print(f"    Extrahiert: brand={brand}, model={model}, gb={gb}, color={color}")
                
                if not brand or not model:
                    print(f"    FEHLER: Modell nicht erkannt")
                    break
                
                vk_link = get_vk_url(brand, model)
                print(f"    VK URL: {vk_link}")
                
                driver.get(vk_link)
                human_pause()
                
                preis = click_variation(driver, gb, color)
                
                # Erfolgreich! Retry-Schleife verlassen
                if preis > 0:
                    break
                else:
                    print(f"    Preis nicht gefunden - Versuch {retry+2}/{max_retries}")
                    time.sleep(5)
                    
            except Exception as e:
                print(f"    FEHLER: {e} - Versuch {retry+2}/{max_retries}")
                time.sleep(5)
                continue
        
        if preis > 0:
            preis_mindert = round(preis * 0.9, 2)
            variation = f"{color} {gb}" if color and gb else gb or color
            print(f"    Preis: {preis} EUR -> {preis_mindert} EUR [{variation}]")
            
            all_results.append({
                "VK LINK": vk_link,
                "SKU": sku,
                "Preis (-10%)": preis_mindert,
                "Variation": variation
            })
        else:
            print(f"    FEHLER: Preis nicht gefunden - warte und weiter...")
            time.sleep(10)  # Länger warten bei Fehler
        
        # Sofort in Excel speichern (nach jedem Produkt)
        if all_results:
            result_df = pd.DataFrame(all_results)
            result_df.to_excel(OUTPUT_FILE, index=False)
        
        time.sleep(random.uniform(5, 10))
    
    # Zweiter Durchgang: Fehlgeschlagene Produkte nochmal versuchen
    print("\n[*] Zweiter Durchgang für fehlgeschlagene Produkte...")
    failed_skus = set()
    for r in all_results:
        if r["Preis (-10%)"] == 0 or r["Preis (-10%)"] == 0.0:
            failed_skus.add(r["SKU"])
    
    if failed_skus:
        print(f"    {len(failed_skus)} Produkte werden erneut versucht...")
        
        for idx, row in df.iterrows():
            sku = row['sku']
            if sku not in failed_skus:
                continue
            
            name = row['Name']
            url_scrape = str(row['url scrape'])
            
            print(f"\n[2. Versuch] {name}")
            
            for retry in range(2):  # 2 weitere Versuche
                try:
                    brand, model, gb, color = extract_all_from_url(url_scrape)
                    if not brand or not model:
                        break
                    
                    vk_link = get_vk_url(brand, model)
                    driver.get(vk_link)
                    human_pause()
                    
                    preis = click_variation(driver, gb, color)
                    
                    if preis > 0:
                        preis_mindert = round(preis * 0.9, 2)
                        variation = f"{color} {gb}" if color and gb else gb or color
                        print(f"    Preis: {preis} EUR -> {preis_mindert} EUR [{variation}]")
                        
                        # Suchen und aktualisieren oder hinzufügen
                        found = False
                        for i, r in enumerate(all_results):
                            if r["SKU"] == sku:
                                all_results[i]["Preis (-10%)"] = preis_mindert
                                all_results[i]["Variation"] = variation
                                found = True
                                break
                        
                        if not found:
                            all_results.append({
                                "VK LINK": vk_link,
                                "SKU": sku,
                                "Preis (-10%)": preis_mindert,
                                "Variation": variation
                            })
                        
                        # Sofort speichern
                        result_df = pd.DataFrame(all_results)
                        result_df.to_excel(OUTPUT_FILE, index=False)
                        break
                    else:
                        time.sleep(3)
                except Exception as e:
                    print(f"    FEHLER: {e}")
                    time.sleep(3)
                    continue
    
    if all_results:
        result_df = pd.DataFrame(all_results)
        result_df.to_excel(OUTPUT_FILE, index=False)
        print(f"\nFertig! {len(all_results)} Ergebnisse: {OUTPUT_FILE}")
    
    driver.quit()


if __name__ == "__main__":
    main()