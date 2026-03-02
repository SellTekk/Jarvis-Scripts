---
name: project-shield
description: "Projekt-Schutz-System: Schützt Projekte vor versehentlicher Zerstörung durch KI-Agenten + Session-übergreifendes Gedächtnis. Automatisch aktivieren bei: (1) Arbeit in einem neuen Projekt-Ordner, (2) Wenn README.md oder CHANGELOG.md vorhanden sind, (3) Bevor Dateien erstellt oder geändert werden, (4) Nach jedem erfolgreichen Task/Aufgabe. WICHTIG: Immer CHANGELOG.md aktualisieren nach Änderungen, README.md NIE überschreiben. Für Session-Continuity: .project-context.md nutzen."
---

# project-shield

Schützt Projekte mit README.md (Quelle der Wahrheit), CHANGELOG.md (Historie) und .project-context.md (Session-übergreifend).

## WANN VERWENDEN

Dieser Skill sollte **automatisch** verwendet werden bei:
- Jede Arbeit in einem neuen Projekt-Ordner
- Vor dem Erstellen neuer Dateien
- Nach dem Abschluss von Aufgaben/Änderungen
- Wenn CHANGELOG.md existiert → immer aktualisieren

## Session-Übergreifendes Gedächtnis

### .project-context.md

Wenn du in einem Projekt-Ordner arbeitest, prüfe OBEN:

1. **Beim Session-Start:** Gibt es `.project-context.md`?
   - JA → Lesen! Sage dem User: "Letzte Session war bei X, mache weiter bei Y"
   - NEIN → Eventuell neu erstellen (wenn Projekt noch nicht bekannt)

2. **Nach jeder Aufgabe:** Aktualisiere `.project-context.md`:
   ```markdown
   # Projekt: <Name>
   Letzte Session: 2026-02-27 18:00
   Agent: main

   ## Stand
   - Parser.py → 80% fertig, Problem bei Zeile 45
   - Nächster Schritt: Selenium-Crawler debuggen

   ## Bekannte Probleme
   - AttributeError bei .product
   ```

## CHANGELOG.md Regeln

- **NEUE** Einträge immer oben hinzufügen
- **NIEMALS** README.md überschreiben
- Format:
   ```markdown
   ## [Datum]
   - Neue Funktion X implementiert
   - Bug Y behoben
   - Refactoring bei Z
   ```

## Für alle Agenten

Dieser Skill gilt für ALLE Agenten im OpenClaw System.
