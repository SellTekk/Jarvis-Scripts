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
    print("=== VK Preis-Crawler v5.0 ===")
    
    df = pd.read_excel(INPUT_FILE)
    print(f"Zeilen: {len(df)}")
    
    # Test mit ersten 3
    df = df.head(3)
    
    options = Options()
    options.add_argument("--start-maximized")
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    
    all_results = []
    
    for idx, row in df.iterrows():
        name = row['Name']
        url_scrape = str(row['url scrape'])
        sku = row['sku']
        
        print(f"\n[{idx+1}] {name}")
        
        brand, model, gb, color = extract_all_from_url(url_scrape)
        print(f"    Extrahiert: brand={brand}, model={model}, gb={gb}, color={color}")
        
        if not brand or not model:
            print(f"    FEHLER: Modell nicht erkannt")
            continue
        
        vk_link = get_vk_url(brand, model)
        print(f"    VK URL: {vk_link}")
        
        driver.get(vk_link)
        human_pause()
        
        preis = click_variation(driver, gb, color)
        
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
            print(f"    FEHLER: Preis nicht gefunden")
        
        time.sleep(random.uniform(5, 10))
    
    if all_results:
        result_df = pd.DataFrame(all_results)
        result_df.to_excel(OUTPUT_FILE, index=False)
        print(f"\nFertig! {len(all_results)} Ergebnisse: {OUTPUT_FILE}")
    
    driver.quit()


if __name__ == "__main__":
    main()