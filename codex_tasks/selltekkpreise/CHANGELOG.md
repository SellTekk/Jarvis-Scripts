# CHANGELOG - SelltekkPreise Crawler

## [2026-03-08]
- **FIX**: Inventory Check - jetzt mit vollständigem Produktnamen-Matching
- **FIX**: Idealo Workflow V6 - direkte Produkt-Links aus Suchergebnissen (kein Klick nötig)
- **FEATURE**: Neue Idealo HTML-Struktur implementiert (direkte OffersOfProduct Links)
- **FIX**: X/XS/XR Erkennung im Inventory (Modell ohne Nummer)
- **FIX**: iPhone Air Erkennung (17 Air)
- **FIX**: Pro Max, Plus, e Erkennung verbessert
- **FIX**: Farben aus Idealo HTML extrahiert (keine Hardcoded Liste)
- **FIX**: Preise aus Idealo HTML extrahiert (kein Fallback mehr)
- **FIX**: Bilder aus Idealo für Parent und jede Variation
- **FIX**: 30% Rabatt auf Idealo-Preis (0.7 Faktor)
- **FIX**: SKU-Konflikt gelöst (UUID-basierte SKUs)
- **FIX**: inventory_check.py optimiert (alle 2000 Produkte, sortiert nach neuesten)
- **FIX**: MIN_MODELLE = 11 (iPhone 11+)
- **FEATURE**: Tab-Wechsel für Idealo-Anfragen (Blockierung vermeiden)
- **FIX**: iPhone SE Erkennung (SE 2022/2020 werden jetzt verarbeitet)
- **FEATURE**: Browser startet automatisch via OpenClaw API
- **FIX**: run.py generiert SKU aus URL (vorher fehlte)
- **FIX**: product_builder.py nutzt idealo_url statt url
- **FEATURE**: Alle 5 Zustände als Variationen (Neuware=publish, andere=draft)
- **FEATURE**: Zustands-Bilder für gebrauchte Geräte (Wie-Neu, Sehr-Gut, etc.)
- **FEATURE**: Kategorien erhalten Bilder beim Erstellen
- **FEATURE**: Samsung Support erweitert:
  - MIN_MODELLE = S21 (war S22)
  - Xcover Serie unterstützt
  - Flip/Fold Serien erkannt
  - FE, Edge erkannt
  - Enterprise Edition wird gefiltert
  - A/M Serien vollständig unterstützt

## [2026-03-07]
- Initialer Workflow Aufbau
