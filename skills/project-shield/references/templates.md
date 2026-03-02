# Templates für project-shield

## README.md Template

```markdown
# Projekt-Name

## Projekt-Ziel
> Kurze Beschreibung was das Projekt macht und warum es existiert

## Funktionen
- Funktion 1
- Funktion 2
- Funktion 3

## Tech-Stack
- Python 3.10+
- ...

## Installation
1. Clone repo
2. `pip install -r requirements.txt`
3. ...

## Nutzung
```bash
python main.py
```

## Regeln für Agenten (NICHT überschreiben!)
- README.md ist die "Quelle der Wahrheit"
- NIE diesen Abschnitt überschreiben
- Änderungen in CHANGELOG.md dokumentieren

---
**Letzte Änderung:** YYYY-MM-DD HH:MM
```

## CHANGELOG.md Template

```markdown
# Changelog
Alle Änderungen werden chronologisch festgehalten. Nichts wird gelöscht.

---

## [YYYY-MM-DD HH:MM] Kurze Beschreibung
- Kategorie: handys|openclaw|skill|...
- Änderung: Was wurde gemacht
- Agent: Name des Agenten
- Details: Zusätzliche Info
```

## CHANGELOG Regeln

1. **NUR appenden** - Niemals bestehende Einträge löschen
2. **Immer oben anfügen** - Neueste zuerst
3. **Jeder Eintrag braucht:**
   - Datum/Zeit
   - Kurze Beschreibung
   - Kategorie (optional)
   - Agent-Name (wer hat es gemacht)
4. **Keine Leerzeilen löschen** - Chronologie muss erhalten bleiben

## Agenten-Regeln

### DOS ✓
- Lese README.md VOR jeder Arbeit
- Prüfe CHANGELOG.md bevor du etwas änderst
- Hänge neue Änderungen an CHANGELOG.md an

### DON'TS ✗
- NIE README.md überschreiben (nur Benutzer)
- NIE CHANGELOG-Einträge löschen
- NIE bestehende Einträge ändern
- NIE die Struktur des CHANGELOG ändern