# Codex Task Seed

Task:

Verbessere das WooCommerce Upload Script in codex_tasks/selltekkpreise:

1. Script bleibt oft hängen - brauche robustere Fehlerbehandlung mit Retry-Logik
2. Erstelle ALLE 30 Variationen (6 Farben/Speicher × 5 Zustände) in EINEM Durchgang
3. Füge Fortschrittsanzeige hinzu (X/30 erstellt)
4. Bei Fehlern: nur fehlende Variationen nacherstellen, nicht alles neu

WICHTIG: Das Script woo_variable_uploader.py muss alle 30 Variationen auf einmal erstellen können.
