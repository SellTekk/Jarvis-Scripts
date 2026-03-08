# Codex Task

Task:

Verbessere das WooCommerce Upload Script in F:\Crawlerv3\auto-discovery\woo_variable_uploader.py:

1. Script bleibt oft hängen - brauche robustere Fehlerbehandlung mit Retry-Logik (HTTPAdapter mit Backoff)
2. Erstelle ALLE 30 Variationen (6 Farben/Speicher × 5 Zustände) in EINEM Durchgang
3. Füge Fortschrittsanzeige hinzu (X/30 erstellt)
4. Bei Fehlern: nur fehlende Variationen nacherstellen, nicht alles neu

WICHTIG: 
- Du musst PUSHEN können! Nutze 'git push -u origin codex-XXXX' nach dem Commit
- Wenn Push nicht geht: poste die Änderungen als Patch/Kommentar im Issue

File:
woo_variable_uploader.py
