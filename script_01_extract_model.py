import re

def extract_model_from_handyverkauf(url):
    \"\"\"
    Extrahiert Modell aus handyverkauf.net URL
    Bsp: https://www.handyverkauf.net/apple-iphone-14-128gb-blau_h_10788
    → Brand: apple
    → Model: iphone14
    \"\"\"
    # Extrahiere den Teil zwischen /net/ und _h_
    match = re.search(r'/net/([a-z0-9-]+)_h_', url)
    if not match:
        return None, None
    
    name = match.group(1)  # apple-iphone-14-128gb-blau
    
    # Extrahiere Marke (erstes Wort)
    brand = name.split('-')[0]  # apple
    
    # Extrahiere Modell (zweiter Teil bis zur Zahl)
    # apple-iphone-14-128gb-blau → iphone14
    parts = name.split('-')
    if len(parts) >= 2:
        # iphone-14-128gb-blau
        model_part = '-'.join(parts[1:])
        # Finde die Modellnummer (z.B. 14, 14pro, 13promax)
        model_match = re.match(r'([a-z]+)(\d+)(.*)', model_part)
        if model_match:
            model_base = model_match.group(1)  # iphone
            model_num = model_match.group(2)  # 14
            model_suffix = model_match.group(3)  # -128gb-blau
            
            # Vereinfache: iphone14, iphone14pro, iphone14promax
            # Prüfe auf pro/max
            if 'pro' in model_suffix and 'max' in model_suffix:
                model = f"{model_base}{model_num}promax"
            elif 'pro' in model_suffix:
                model = f"{model_base}{model_num}pro"
            elif 'max' in model_suffix:
                model = f"{model_base}{model_num}max"
            elif 'mini' in model_suffix:
                model = f"{model_base}{model_num}mini"
            elif 'plus' in model_suffix:
                model = f"{model_base}{model_num}plus"
            elif 'air' in model_suffix:
                model = f"{model_base}{model_num}air"
            elif 'e' in model_suffix[:3]:  # iphone16e
                model = f"{model_base}{model_num}e"
            else:
                model = f"{model_base}{model_num}"
        else:
            model = model_part
    else:
        model = name
    
    return brand, model

# Test
test_urls = [
    "https://www.handyverkauf.net/apple-iphone-14-128gb-blau_h_10788",
    "https://www.handyverkauf.net/apple-iphone-14-128gb-mitternacht_h_10786",
    "https://www.handyverkauf.net/apple-iphone-16-pro-256gb-schwarz_h_12345",
]

for url in test_urls:
    brand, model = extract_model_from_handyverkauf(url)
    print(f"URL: {url}")
    print(f"  → Brand: {brand}, Model: {model}")
    print(f"  → VK URL: https://www.verkaufen.de/handy-verkaufen/{brand}/{model}/")
    print()
