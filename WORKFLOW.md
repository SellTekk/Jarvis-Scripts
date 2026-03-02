# Workflow: Preis-Crawler für RELEASE.xlsx

## Ziel
Excel-Datei mit Produkten von handyverkauf.net einlesen, auf verkaufen.de finden, Preise crawlen und 10% abziehen.

## Input
- `F:/crawlerv5/RELEASE.xlsx`
- Spalten: `Name`, `url scrape` (handyverkauf.net), `sku`

## Output
- Neue Excel-Datei mit:
  - **A:** VK LINK (verkaufen.de Link) - zur SKU zugeordnet
  - **B:** SKU (aus Release.xlsx)
  - **C:** (-10%) Preis (Neuware-Preis minus 10%)

## Schritt-für-Schritt

### 1. Excel einlesen
```python
df = pd.read_excel('F:/crawlerv5/RELEASE.xlsx')
```

### 2. Produkt identifizieren
- Aus `url scrape` (handyverkauf.net) Produktnamen extrahieren
- Bsp: `https://www.handyverkauf.net/apple-iphone-air-1tb-himmelblau_h_13086` → "Apple iPhone Air 1TB Himmelblau"

### 3. Auf verkaufen.de suchen
- Suchbegriff: Produktname
- URL: `https://www.verkaufen.de/?s={suchbegriff}`

### 4. Passendes Produkt finden
- Element finden, das zu Farbe/Speicher passt
- Link extrahieren

### 5. Preis crawlen (Neuware)
- Auf verkaufen.de Produktseite öffnen
- Zustand "Neuware" auswählen
- Preis auslesen

### 6. Preis mindern
- 10% vom Neuware-Preis abziehen
- `preis_mindert = preis * 0.9`

### 7. In Excel speichern
- A: VK LINK
- B: SKU
- C: (-10%) Preis

## Technische Details
- Browser: **sichtbar** (nicht headless)
- Pausen: 3-5 Sekunden zwischen Requests
- Tool: OpenClaw Browser oder Selenium mit sichtbarem Fenster

## Erweiterungen (später)
- Alle Zustände crawlen (Neuware, Wie neu, etc.)
- Automatische Wiederholung bei Fehlern
- Fortschrittsanzeige