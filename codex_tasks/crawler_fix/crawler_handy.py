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

# === KONFIGURATION ===
# Wähle: "handy" oder "tablet"
PRODUKT_TYP = "handy"

if PRODUKT_TYP == "handy":
    INPUT_FILE = "F:/crawlerv5/RELEASE_handy_TB.xlsx"  # TB-Produkte!
    OUTPUT_FILE = "F:/crawlerv5/RELEASE_handy_ergebnis.xlsx"
elif PRODUKT_TYP == "tablet":
    INPUT_FILE = "F:/crawlerv5/RELEASE_tablet.xlsx"
    OUTPUT_FILE = "F:/crawlerv5/RELEASE_tablet_ergebnis.xlsx"

VERKAUFEN_BASE = "https://www.verkaufen.de"

# Proxy - auskommentieren wenn nicht benoetigt
PROXY = "localhost:9999"  # proxy-chain Server

# URL-Mapping für Modelle die nicht mehr unter alter URL existieren
# Format: "alter_model_name": "neue_url_suffix"
MODEL_URL_MAP = {
    # Galaxy Z Fold Serie - KORREKTE URLs (keine Bindestriche!)
    "galaxyzfold4": "galaxyzfold45g",  # 5G Version
    "galaxyzfold44g": "galaxyzfold44g",  # 4G Version
    "galaxyzfold3": "galaxyzfold35g",
    "galaxyzfold2": "galaxyzfold25g",
    "galaxyzfold": "galaxyzfold5g",
    # Galaxy Z Flip Serie - KORREKTE URLs
    "galaxyzflip4": "galaxyzflip4",
    "galaxyzflip3": "galaxyzflip3",
    "galaxyzflip": "galaxyzflip",
    # Apple iPhone Plus Serie - "+" -> "plus"
    "iphone14+": "iphone14plus",
    "iphone13+": "iphone13plus",
    "iphone12+": "iphone12plus",
}

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
                
                # SPEZIALFALL: "thinkphone256gb" - GB ist im gleichen Wort wie Zahl
                # Extrahiere Zahl und GB aus dem Teil
                if 'gb' in p.lower() or 'tb' in p.lower():
                    # Trenne "256gb" in "256" und "gb"
                    num_match = re.search(r'(\d+)', p)
                    if num_match:
                        model_num = num_match.group(1)
                        has_gb = True  # GB ist in diesem Teil
                    else:
                        model_num = p
                        has_gb = False
                else:
                    model_num = p
                    has_gb = False
                
                suffix = '-'.join(parts[i+1:]) if i+1 < len(parts) else ''
                
                model = model_base + model_num
                
                # Wenn GB im model_num war, als suffix merken für später
                if has_gb:
                    suffix = 'gb' + ('-' + suffix if suffix else '')
                
                # Spezielle Modelle: flip, z, fold erkennen (auch im model_base!)
                if model_base in ['flip', 'z'] or 'flip' in model_base:
                    model = 'galaxyzflip' + model_num
                elif 'fold' in model_base:
                    model = 'galaxyzfold' + model_num
                elif model_base in ['ultra']:
                    # ultra ist schon im model_base (z.B. von "s22ultra"), nichts tun
                    pass
                elif model_base in ['duo', 'surface'] and 'duo' in model_base:
                    # Surface Duo - nur "duo" als Modellname!
                    model = 'duo'
                elif model_base in ['xiaomi', 'mi'] and brand in ['xiaomi', 'mi']:
                    # Xiaomi/MI特殊情况: "xiaomi 13 pro" -> "mi13pro" NICHT "xiaomi13pro"
                    model = 'mi' + model_num
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
                model_suffix = ['pro', 'max', 'mini', 'plus', 'air', 'ultra', 'promax', 'flip', 'z', '5g', '4g', '5g+', '4g+', 'se', 'fe', 'ee', 'sm', 'sm-a', 'sm-', 'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'a8', 'a9', 'gb', 'tb', 'lite', 'lite5g', 'pro5g']
                remaining = [p for p in remaining if p.lower() not in model_suffix and not p.lower().startswith('sm-') and not p.lower().startswith('sm-a')]
                
                # SPEZIALFALL: GB im Modellnamen (z.B. "thinkphone256gb")
                # Extrahiere GB aus model_num falls vorhanden
                if has_gb and not gb:
                    num_match = re.search(r'(\d+)\s*(gb|tb)', p.lower())
                    if num_match:
                        gb = num_match.group(1).upper() + num_match.group(2).upper()
                        model = model  # Modell ohne GB behalten
                
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
    # Prüfe ob Modell ein Mapping hat
    url_model = MODEL_URL_MAP.get(model, model)
    return f"{VERKAUFEN_BASE}/handy-verkaufen/{brand}/{url_model}/"


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
                    # Check for both "256" and "256GB" and "256 GB" and "256TB" / "256 TB"
                    if num >= 32 and (
                        f'{num}' in btn_text or 
                        f'{num}GB' in btn_text or 
                        f'{num} GB' in btn_text or
                        f'{num}TB' in btn_text or
                        f'{num} TB' in btn_text or
                        f'{num}gb' in btn_text.lower() or
                        f'{num}tb' in btn_text.lower()
                    ):
                        gb_btn = btn
            
            # Farbe-Button - mit dynamischer Erkennung UND Alias-Mapping
            if color:
                # Farb-Alias-Mapping (Deutsch -> Deutsch + Englisch Synonyme)
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
                
                btn_lower = btn_text.lower()
                color_lower = color.lower()
                
                # Prüfe Farbe matchen - nur wenn unser gesuchtes Farbwort im Button ODER Button-Farbe in unseren bekannten Farben
                matched = False
                
                # Hole die Alias-Liste für die gesuchte Farbe
                target_aliases = None
                for main_color, aliases in color_aliases.items():
                    if color_lower in aliases:
                        target_aliases = aliases
                        break
                
                if target_aliases:
                    # Prüfe ob einer der Ziel-Aliasse im Button-Text vorkommt
                    for alias in target_aliases:
                        if alias in btn_lower:
                            color_btn = btn
                            matched = True
                            break
                
                # Fallback: einfache Teilstring-Suche (wenn kein Alias match)
                if not matched:
                    if color_lower in btn_lower or btn_lower in color_lower:
                        color_btn = btn
        
        print(f"      Suche GB={gb}, Farbe={color}")
        
        if gb_btn:
            print(f"      Klicke GB: {gb_btn.text}")
            driver.execute_script("arguments[0].click();", gb_btn)
            time.sleep(2)  # Warten bis Preis lädt
        
        if color_btn:
            print(f"      Klicke Farbe: {color_btn.text}")
            driver.execute_script("arguments[0].click();", color_btn)
            time.sleep(3)  # Warten bis Preis lädt (wichtig für React!)
        
        # Nochmal kurz warten
        time.sleep(2)
        
        # Erst JETZT Seite prüfen
        page = driver.page_source
        
        # Prüfe zuerst ob Seite existiert (nicht 404)
        if "Seite nicht gefunden" in page or "existiert nicht" in page.lower():
            print(f"      FEHLER: Seite existiert nicht (404)")
            return -1  # Spezieller Wert für "Seite nicht gefunden"
        
        # Prüfe ob überhaupt Angebote vorhanden
        if "keine angebot" in page.lower() or "keine angebote" in page.lower() or "kein angebot" in page.lower():
            print(f"      ℹ️ Keine Angebote für dieses Modell")
            return -2  # Keine Angebote
        
        # Prüfe ob Seite geladen aber kein Preis (alter/seltener Artikel)
        # Nach Klick auf GB+Farbe: wenn kein Preis sichtbar = zu alt/nicht ankaufbar
        if 'configuration-option' in page:
            # Seite hat Konfigurator - prüfe ob Preis nach Klick erscheint
            # Wir sind hier NACH dem Klick - wenn 0.0 zurückkommt, wars kein Preis
            pass
        
        # Prüfe ob "kein Einkaufspreis bekannt" - ABER erst NACH dem Preis-Check!
        # Erst prüfen OB es einen Preis gibt, DANN erst "kein Preis" melden
        preis = None
        match = re.search(r'Ankaufspreis f.r Neuware\s*([\d.,]+)', page)
        if match:
            preis_str = match.group(1)
            # European format: 1.005,30 or 1,005.30 - remove thousand separators
            preis_str = preis_str.replace('.', '').replace(',', '.')
            try:
                preis = float(preis_str)
                return preis if preis > 10 else 0.0
            except:
                return 0.0
        
        # NUR wenn kein Preis gefunden wurde - DANN "kein Einkaufspreis" prüfen
        if "kein einkaufspreis" in page.lower() or "kein ankaufspreis" in page.lower() or "nicht ankaufbar" in page.lower():
            print(f"      ℹ️ Kein Einkaufspreis bekannt - Gerät wird nicht angekauft")
            return -2  # Keine Angebote
        
        # Wenn wir hier ankommen: Preis nicht gefunden
        # Prüfe ob die Seite überhaupt Konfigurations-Buttons hat (sonst ist es ne 404-Variante)
        if 'configuration-option' not in page:
            return -2  # Keine Angebote/Konfiguration
        
        return 0.0  # Preis nicht gefunden -可能是alt
        
    except Exception as e:
        print(f"      Fehler: {e}")
        return 0.0


def search_product_fallback(driver, brand, model, gb, color):
    """
   Fallback: Wenn URL 404, suche nach Produkt und klicke beste Übereinstimmung
    """
    try:
        print(f"      🔍 Suche Fallback für {brand} {model} {gb} {color}")
        
        # Zur Startseite gehen
        driver.get(VERKAUFEN_BASE)
        human_pause()
        
        # Suchfeld finden (data-slot="input" aria-label)
        search_input = None
        try:
            search_input = driver.find_element(By.CSS_SELECTOR, 'input[data-slot="input"][aria-label*="verkaufen"]')
        except:
            try:
                search_input = driver.find_element(By.CSS_SELECTOR, 'input[placeholder*="verkaufen"]')
            except:
                try:
                    search_input = driver.find_element(By.ID, re.compile('aria.*:.*', re.I))
                except:
                    pass
        
        if not search_input:
            print(f"      ❌ Suchfeld nicht gefunden")
            return None
        
        # Suchbegriff zusammensetzen
        search_term = f"{brand} {model}"
        if gb:
            search_term += f" {gb}"
        if color and color != 'Unbekannt':
            search_term += f" {color}"
        
        # Special characters für Suche bereinigen
        search_term = search_term.replace('+', 'plus').replace('++', 'plusplus')
        
        print(f"      🔍 Suche nach: {search_term}")
        
        # Suchbegriff eingeben
        search_input.clear()
        search_input.send_keys(search_term)
        human_pause()
        
        # Auf Autocomplete-Vorschläge warten
        time.sleep(2)
        
        # Autocomplete-Liste finden (role="option" oder ähnlich)
        suggestions = []
        try:
            suggestions = driver.find_elements(By.CSS_SELECTOR, '[role="option"]')
        except:
            pass
        
        if not suggestions:
            try:
                suggestions = driver.find_elements(By.CSS_SELECTOR, 'ul[role="listbox"] li')
            except:
                pass
        
        if not suggestions:
            try:
                suggestions = driver.find_elements(By.CSS_SELECTOR, '.autocomplete li')
            except:
                pass
        
        if not suggestions:
            print(f"      ❌ Keine Vorschläge gefunden")
            return None
        
        # Beste Übereinstimmung finden - muss Modell enthalten!
        best_match = None
        best_score = 0
        
        # Extrahiere die Nummer aus dem Ziel-Modell (z.B. "a23" aus "galaxya23")
        target_model = model.lower().replace('galaxy', '').replace('samsung', '')  # z.B. "a23" oder "s23+"
        target_num = ''.join(c for c in target_model if c.isdigit())  # z.B. "23"
        
        for suggestion in suggestions:
            text = suggestion.text.lower()
            score = 0
            
            # WICHTIG: A-Serie vs S-Serie unterscheiden!
            is_target_a_series = 'galaxya' in model.lower()
            is_target_s_series = 'galaxys' in model.lower()
            
            if is_target_a_series:
                # Für A-Serie: MUSS "a" + nummer haben, KEIN "s" + nummer
                has_a_match = 'a' + target_num in text
                has_s_match = 's' + target_num in text
                
                if has_a_match and not has_s_match:
                    score += 50  # Sehr hohe Priorität
                elif 'galaxy a' in text:
                    score += 40
                # Bestrafung für falsche Serie
                elif has_s_match:
                    score -= 100  # Negativ - falsche Serie!
                    
            elif is_target_s_series:
                # Für S-Serie: MUSS "s" + nummer haben, KEIN "a" + nummer
                has_s_match = 's' + target_num in text
                has_a_match = 'a' + target_num in text
                
                if has_s_match and not has_a_match:
                    score += 50  # Sehr hohe Priorität
                elif 'galaxy s' in text:
                    score += 40
                # Bestrafung für falsche Serie
                elif has_a_match:
                    score -= 100  # Negativ - falsche Serie!
            
            # Apple iPhone: "iphone14+" -> "iphone 14" ODER "iphone 14 plus"
            elif 'iphone' in model.lower():
                model_num = ''.join(c for c in model.lower() if c.isdigit())
                # Check for "iphone 14" or "iphone 14 plus"
                if 'iphone' in text and model_num in text:
                    score += 50  # Grundmatch
                    # Extra für Plus
                    if 'plus' in model.lower() or '+' in model:
                        if 'plus' in text:
                            score += 10
                    # Kein anderes Modell
                    if 'iphone ' + str(int(model_num)+1) in text or 'iphone' + str(int(model_num)+1) in text:
                        score -= 100  # Z.B. iPhone 14 vs iPhone 15
            else:
                # Andere Marken - Standard matching
                if brand.lower() in text:
                    score += 10
                if model.lower().replace('x30', 'x 30') in text or model.lower() in text.replace(' ', ''):
                    score += 20
            
            if score > best_score:
                best_score = score
                best_match = suggestion
        
        if best_match and best_score >= 40:  # 100% Match (50) oder guter Apple Match (40+)
            print(f"      ✅ Klicke: {best_match.text[:50]}")
            driver.execute_script("arguments[0].click();", best_match)
            human_pause()
            return driver.current_url
        elif suggestions:
            # Kein guter Match - NUR 100% Match erlaubt!
            # Überspringen statt falsches Modell klicken!
            print(f"      ⚠️ Kein 100% Match (Modelldetails stimmen nicht) - überspringe")
            return None
        
        return None
        
    except Exception as e:
        print(f"      ❌ Fallback Fehler: {e}")
        return None


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
                # NUR überspringen wenn Preis > 0!
                # Produkte mit Preis=0 werden neu gecrawlt
                preis = r["Preis (-10%)"]
                if preis > 0:
                    all_results.append({
                        "VK LINK": r["VK LINK"],
                        "SKU": r["SKU"],
                        "Preis (-10%)": preis,
                        "Variation": r["Variation"]
                    })
                    processed_skus.add(r["SKU"])
            print(f"[*] {len(processed_skus)} bereits verarbeitete SKUs mit Preis gefunden")
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
                elif preis == -1:
                    # Seite existiert nicht - Such-Fallback versuchen
                    print(f"      🔄 Versuche Such-Fallback...")
                    fallback_url = search_product_fallback(driver, brand, model, gb, color)
                    if fallback_url:
                        print(f"      ✅ Fallback URL gefunden: {fallback_url}")
                        # Erneut versuchen mit der neuen URL
                        human_pause()
                        preis = click_variation(driver, gb, color)
                        if preis > 0:
                            vk_link = fallback_url  # Update VK-Link mit gefundener URL
                            break
                        elif preis == -1:
                            print(f"    FEHLER: Fallback auch 404 - überspringe")
                            break
                        elif preis == -2:
                            print(f"    FEHLER: Fallback hat keine Angebote - überspringe")
                            break
                    else:
                        print(f"    FEHLER: Kein Fallback gefunden - überspringe")
                        break
                elif preis == -2:
                    # Keine Angebote - sofort überspringen
                    print(f"    ℹ️ Keine Angebote - überspringe")
                    break
                else:
                    # preis == 0.0 - Preis nicht gefunden
                    # Nach 2 Versuchen: annehmen dass Gerät zu alt ist
                    if retry >= 1:
                        print(f"    ℹ️ Kein Preis nach {retry+1} Versuchen - Gerät zu alt/not supported")
                        preis = -2  # Als "keine Angebote" markieren
                        break
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
        elif preis == -1:
            # Seite existiert nicht - nicht speichern
            print(f"    ÜBERSPRUNGEN: Seite existiert nicht")
        elif preis == -2:
            # Keine Angebote - SPEICHERN mit Preis 0 damit es übersprungen wird!
            print(f"    ÜBERSPRUNGEN: Keine Angebote verfügbar")
            all_results.append({
                "VK LINK": vk_link,
                "SKU": sku,
                "Preis (-10%)": 0,
                "Variation": "KEIN ANKAUF"
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