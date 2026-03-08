"""
WooCommerce Variable Products Uploader

Erstellt Variable Products mit:
- Parent: Type = variable
- Attribute: Speicher, Farbe, Zustand (als Dropdowns)
- Variationen: Jede Kombination mit eigenem Preis

Basiert auf dem CSV-Format aus idealo_crawler_varianten_ready_bilderzuvariaten.py
"""

import os
import sys
import json
import time
import requests
import re
from datetime import datetime

# === BASE DIR ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# === WOOCOMMERCE CONFIG ===
WC_CK = "ck_6b947bafda50e508976a407186d1e7fade4a6a0f"
WC_CS = "cs_d6ed242dc239723dc2159a3a17b570e38a4392a8"
WC_URL = "https://sell-tekk.de/wp-json/wc/v3"

CONFIG_FILE = os.path.join(BASE_DIR, "output", "woo_config.json")
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
        WC_URL = config.get('shop_url', WC_URL) + '/wp-json/wc/v3'
        WC_CK = config.get('consumer_key', WC_CK)
        WC_CS = config.get('consumer_secret', WC_CS)


def get_auth():
    return (WC_CK, WC_CS)


# ============================================================
# ZUSTÄNDE (wie im Original)
# ============================================================
ZUSTAENDE = [
    {"label": "Neuware", "suffix": ""},
    {"label": "Wie-Neu", "suffix": "WIE-NEU"},
    {"label": "Sehr-Gut", "suffix": "SEHRGUT"},
    {"label": "Gut", "suffix": "GUT"},
    {"label": "Akzeptabel", "suffix": "AKZEPTABEL"},
]

# === Zustands-Bilder ===
CONDITION_IMAGE_MAP = {
    "Wie-Neu":      "http://sell-tekk.de/wp-content/uploads/2025/08/Wie-Neu.png",
    "Sehr-Gut":     "http://sell-tekk.de/wp-content/uploads/2025/08/Sehr-Gut.png",
    "Gut":          "http://sell-tekk.de/wp-content/uploads/2025/08/Gut.png",
    "Akzeptabel":   "http://sell-tekk.de/wp-content/uploads/2025/08/akzeptabel.png",
}


# ============================================================
# SEO (wie zuvor)
# ============================================================

def generate_keywords(name, farbe, speicher):
    name_clean = name.replace(" verkaufen", "").strip()
    keywords = [
        name_clean, f"{name_clean} verkaufen",
        f"{name_clean} {farbe}", f"{name_clean} {speicher}",
        "Smartphone verkaufen", "Handy verkaufen",
        "Ankauf", "Sofortauszahlung", "Deutschland"
    ]
    return ", ".join(keywords[:8])


def generate_seo(name, farbe, speicher):
    name = (name or "").replace(" verkaufen", "").strip()
    
    meta_titel = (
        f"{name} {farbe} {speicher} verkaufen | Top-Ankaufpreise Deutschland + Bremen | "
        f"Sofortauszahlung in 6 Stunden | größte Plattform Norddeutschland"
    )
    
    meta_desc = (
        f"{name} {farbe} {speicher} verkaufen? Wir bieten die höchsten Ankaufpreise in ganz Deutschland! "
        "Sofortauszahlung innerhalb 6 Stunden, kostenloser Versand. "
        "Die größte Ankaufsplattform in Bremen, Hamburg, Hannover & Norddeutschland. "
        "Jetzt verkaufen - innerhalb 6 Stunden Geld auf dein Konto!"
    )
    
    og_desc = f"{name} {farbe} {speicher} verkaufen - Sofortauszahlung 6Std - Top-Preise"
    
    kw = generate_keywords(name, farbe, speicher)
    
    description = f"""
Verkaufe dein {name} {farbe} mit {speicher} Speicher jetzt einfach und sicher an SellTekk.

✅ Sofortauszahlung innerhalb von 6 Stunden
✅ Kostenloser Versand mit DHL
✅ Faire Bewertung
✅ Sicherer Datentransfer
✅ Größte Ankaufsplattform Bremen, Hamburg, Hannover
✅ Über 10.000 zufriedene Kunden

Bremen | Hamburg | Hannover | Deutschlandweite Top-Preise
""".strip()
    
    schema = json.dumps({
        "@context": "https://schema.org",
        "@type": "Product",
        "name": f"{name} {farbe} {speicher}",
        "description": meta_desc,
        "offers": {"@type": "Offer", "priceCurrency": "EUR", "price": "0", "availability": "https://schema.org/InStock"}
    })
    
    return {"meta_titel": meta_titel, "meta_desc": meta_desc, "keywords": kw, 
            "description": description, "og_desc": og_desc, "schema_product": schema}


def parse_variant_info(text):
    """Extrahiert Farbe und Speicher"""
    farbe, speicher = "", ""
    
    storage_match = re.search(r'(\d+)\s*(GB|TB|MB)', text, re.IGNORECASE)
    if storage_match:
        speicher = f"{storage_match.group(1)} {storage_match.group(2).upper()}"
    
    colors = ["Schwarz", "Weiß", "Blau", "Rot", "Grün", "Gold", "Silber", "Grau", "Titan", "Lila", "Rosa", "Hellblau", "Hellrosa", "White", "Black", "Green", "Purple", "RED", "Yellow"]
    for c in colors:
        if c.lower() in text.lower():
            farbe = c
            break
    
    return farbe, speicher


# ============================================================
# VARIABLE PRODUCT ERSTELLEN
# ============================================================

def create_variable_product(product_data: dict, with_seo: bool = True) -> dict:
    """
    Erstellt ein Variable Product mit Attributen und allen Variationen.
    """
    name = product_data.get('name', 'Unbekannt')
    # SKU generieren wenn nicht vorhanden - IMMER neu generieren!
    import uuid
    sku_base = f"VAR-{uuid.uuid4().hex[:10].upper()}"
    
    preise = product_data.get('preise', {})  # Dict: {(farbe, speicher, zustand): preis}
    varianten = product_data.get('varianten', [])  # Liste: [{farbe, speicher, zustand, preis}, ...]
    categories = product_data.get('categories', [])
    ean = product_data.get('ean', '')
    
    print(f"\n[INFO] Erstelle Variable Product: {name}")
    print(f"       SKU-Basis: {sku_base}")
    
    # Sammle alle Farben und Speicher
    alle_farben = set()
    alle_speicher = set()
    
    for v in varianten:
        if v.get('farbe'):
            alle_farben.add(v['farbe'])
        if v.get('speicher'):
            alle_speicher.add(v['speicher'])
    
    alle_farben = sorted(list(alle_farben))
    alle_speicher = sorted(list(alle_speicher))
    
    print(f"       Farben: {alle_farben}")
    print(f"       Speicher: {alle_speicher}")
    print(f"       Zustände: {len(ZUSTAENDE)}")
    print(f"       Variationen: {len(varianten)}")
    
    # === 1. PARENT PRODUKT ERSTELLEN ===
    # Bild holen aus erster Variante
    bild_url = product_data.get('bild', '')
    if not bild_url and varianten:
        bild_url = varianten[0].get('bild', '')
    
    parent_data = {
        "name": name,
        "sku": sku_base,
        "type": "variable",
        "status": "publish",
        "catalog_visibility": "visible",
        "manage_stock": False,
        "categories": [{"id": c} for c in categories],
        "meta_data": [],
        "images": [{"src": bild_url}] if bild_url else []
    }
    
    # Attribute hinzufügen
    attributes = []
    
    # Speicher
    if alle_speicher:
        attributes.append({
            "name": "Speicher",
            "visible": True,
            "variation": True,
            "options": alle_speicher
        })
    
    # Farbe
    if alle_farben:
        attributes.append({
            "name": "Farbe",
            "visible": True,
            "variation": True,
            "options": alle_farben
        })
    
    # Zustand
    attributes.append({
        "name": "Zustand",
        "visible": True,
        "variation": True,
        "options": [z['label'] for z in ZUSTAENDE]
    })
    
    parent_data["attributes"] = attributes
    
    # SEO
    if with_seo:
        farbe_first = alle_farben[0] if alle_farben else ""
        speicher_first = alle_speicher[0] if alle_speicher else ""
        seo = generate_seo(name, farbe_first, speicher_first)
        
        parent_data["short_description"] = seo["meta_desc"][:150]
        parent_data["description"] = seo["description"]
        parent_data["meta_data"] = [
            {"key": "seo_title", "value": seo["meta_titel"]},
            {"key": "keywords", "value": seo["keywords"]},
            {"key": "schema_product", "value": seo["schema_product"]},
        ]
        if ean:
            parent_data["meta_data"].append({"key": "EAN", "value": ean})
    
    # Parent erstellen
    r = requests.post(f"{WC_URL}/products", auth=get_auth(), json=parent_data)
    
    if not r.ok:
        return {"success": False, "name": name, "error": f"Parent: {r.text[:200]}"}
    
    parent_id = r.json().get('id')
    print(f"       Parent erstellt: ID {parent_id}")
    
    # === 2. VARIATIONEN ERSTELLEN ===
    # Für jede Variante (Farbe+Speicher) alle 5 Zustände erstellen!
    total_created = 0
    for i, v in enumerate(varianten):
        farbe = v.get('farbe', '')
        speicher = v.get('speicher', '')
        preis = v.get('preis', 0)
        
        # 30% Rabatt auf Idealo-Preis!
        if preis and preis > 0:
            preis = round(preis * 0.7, 2)
        else:
            # Fallback
            speicher_gb = int(re.search(r'(\d+)', speicher).group(1)) if speicher and re.search(r'(\d+)', speicher) else 256
            preis = 500 + ((speicher_gb - 256) // 256) * 100
        
        # Bild für diese Variation
        variant_bild = v.get('bild', '')
        
        # Für JEDEN Zustand eine Variation erstellen!
        for zustand_obj in ZUSTAENDE:
            zustand = zustand_obj["label"]
            zustand_kurz = "NW" if zustand == "Neuware" else zustand[:4].upper()
            
            # SKU für Variation
            farbe_kurz = farbe[:3].upper() if farbe else "XXX"
            speicher_kurz = speicher.replace(" ", "").upper() if speicher else "XXX"
            var_sku = f"{sku_base}-{farbe_kurz}-{speicher_kurz}-{zustand_kurz}"
            
            # Status: Nur Neuware = publish, andere = draft
            is_publish = (zustand == "Neuware")
            
            # Bild: Für Neuware = Produktbild, für andere Zustände = Zustands-Bild
            if zustand == "Neuware":
                bild_url = variant_bild if variant_bild else None
            else:
                bild_url = CONDITION_IMAGE_MAP.get(zustand, None)
            
            variation_data = {
                "parent_id": parent_id,
                "sku": var_sku,
                "regular_price": str(preis) if preis else "",
                "status": "publish" if is_publish else "draft",
                "manage_stock": False,
                "attributes": [],
                "image": {"src": bild_url} if bild_url else None
            }
            
            # Attribute für Variation
            if speicher:
                variation_data["attributes"].append({"name": "Speicher", "option": speicher})
            if farbe:
                variation_data["attributes"].append({"name": "Farbe", "option": farbe})
            variation_data["attributes"].append({"name": "Zustand", "option": zustand})
            
            # Variation erstellen
            try:
                r_var = requests.post(f"{WC_URL}/products/{parent_id}/variations", 
                                     auth=get_auth(), json=variation_data, timeout=30)
                
                if r_var.ok:
                    var_id = r_var.json().get('id')
                    status_str = "[PUB]" if is_publish else "[DRAFT]"
                    print(f"       [{total_created+1}] {farbe} {speicher} {zustand} = {preis}€ {status_str} (ID: {var_id})")
                    total_created += 1
                else:
                    error_msg = r_var.text[:100] if r_var.text else "No error message"
                    print(f"       [{total_created+1}] {farbe} {speicher} {zustand} - FEHLER: {r_var.status_code} - {error_msg}")
                    total_created += 1
            except Exception as e:
                print(f"       [{total_created+1}] {farbe} {speicher} {zustand} - EXCEPTION: {str(e)[:50]}")
                total_created += 1
            
            time.sleep(0.3)  # Rate limiting
    
    return {"success": True, "parent_id": parent_id, "name": name, "variationen": total_created}


# ============================================================
# MAIN
# ============================================================

def upload_variable_products(json_file: str, dry_run: bool = True) -> list:
    """Liest JSON und erstellt Variable Products"""
    
    print(f"[INFO] Lese: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    produkte = data.get('produkte', [])
    print(f"[INFO] {len(produkte)} Produkte gefunden\n")
    
    if dry_run:
        print("[DRY RUN] Zeige nur was erstellt werden würde:\n")
        for p in produkte:
            name = p.get('name', 'N/A')
            varianten = p.get('varianten', [])
            print(f"  {name}")
            print(f"    - {len(varianten)} Variationen geplant")
            if varianten:
                farben = set(v.get('farbe', '') for v in varianten)
                speicher = set(v.get('speicher', '') for v in varianten)
                print(f"    - Farben: {sorted(farben)}")
                print(f"    - Speicher: {sorted(speicher)}")
        return []
    
    # Upload
    results = []
    for i, p in enumerate(produkte):
        print(f"\n[{i+1}/{len(produkte)}] ", end="")
        result = create_variable_product(p)
        results.append(result)
        if result.get('success'):
            print(f"  -> OK! Parent ID: {result.get('parent_id')}")
        else:
            print(f"  -> FEHLER: {result.get('error')}")
    
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description='WooCommerce Variable Products Upload')
    parser.add_argument('--input', '-i', default=None)
    parser.add_argument('--dry-run', '-n', action='store_true')
    parser.add_argument('--hersteller', default='apple')
    args = parser.parse_args()
    
    if args.input:
        input_file = args.input
    else:
        input_file = os.path.join(BASE_DIR, 'output', 'test_variable.json')
    
    if not os.path.exists(input_file):
        print(f"[ERROR] Nicht gefunden: {input_file}")
        return 1
    
    results = upload_variable_products(input_file, dry_run=args.dry_run)
    
    if results:
        ok = sum(1 for r in results if r.get('success'))
        print(f"\n=== ERGEBNIS ===")
        print(f"Erfolgreich: {ok}")
        print(f"Fehlgeschlagen: {len(results) - ok}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())