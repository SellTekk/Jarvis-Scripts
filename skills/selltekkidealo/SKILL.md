---
name: selltekkidealo
description: "SellTekk Idealo Crawler - Preisvergleich und WooCommerce-Upload. Verwende für: (1) Produkte zu Idealo hinzufügen mit /selltekkidealo add [kategorie] [URL], (2) Preise crawlen mit /selltekkidealo crawl [kategorie], (3) Produkt einzeln hochladen mit /selltekkidealo produkt [kategorie] [URL], (4) Alle Produkte einer Kategorie hochladen mit /selltekkidealo upload [kategorie], (5) CSV-Export mit /selltekkidealo csv [kategorie], (6) EAN hinzufügen mit /selltekkidealo ean [kategorie], (7) Bilder aktualisieren mit /selltekkidealo bilder [kategorie], (8) SEO-Texte aktualisieren mit /selltekkidealo seo [kategorie], (9) GUI starten mit /selltekkidealo gui [kategorie], (10) Hilfe anzeigen mit /selltekkidealo help"
---

# SellTekk Idealo Crawler

Führt den Crawlerv3 aus, um Produkte von Idealo zu crawlen und zu WooCommerce (sell-tekk.de) hochzuladen.

## Trigger-Wörter

Verwende diesen Skill wenn der Benutzer folgende Befehle eingibt:
- /selltekkidealo
- selltekkidealo
- Idealo Crawler
- Preisvergleich Idealo
- WooCommerce Upload

## Verfügbare Befehle

| Befehl | Beschreibung |
|--------|--------------|
| `/selltekkidealo add [kategorie] [URL]` | Produkt zu Idealo hinzufügen |
| `/selltekkidealo crawl [kategorie]` | Preise crawlen |
| `/selltekkidealo produkt [kategorie] [URL]` | Einzelnes Produkt hochladen |
| `/selltekkidealo upload [kategorie]` | Alle Produkte einer Kategorie hochladen |
| `/selltekkidealo csv [kategorie]` | CSV-Export |
| `/selltekkidealo ean [kategorie]` | EAN hinzufügen |
| `/selltekkidealo bilder [kategorie]` | Bilder aktualisieren |
| `/selltekkidealo seo [kategorie]` | SEO-Texte aktualisieren |
| `/selltekkidealo gui [kategorie]` | GUI starten |
| `/selltekkidealo help` | Hilfe anzeigen |

## Projekt-Pfad

Das Projekt liegt typischerweise unter:
`C:\Users\no\Desktop\Projekte\sell-tekk\crawlerv3\`

## Workflow

1. Python-Skripte im Projektordner ausführen
2. Ergebnisse in WooCommerce hochladen
3. Erfolgsmeldung an User
