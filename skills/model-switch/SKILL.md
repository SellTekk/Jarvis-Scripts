---
name: model-switch
description: Wechselt zwischen free, premium und auto Modellen
user-invocable: true
commands:
  /free: node scripts/switch.js free
  /premium: node scripts/switch.js premium
  /auto: node scripts/switch.js auto
  /model: node scripts/switch.js status
---

# Model Switch Skill

Wechselt zwischen free, premium und auto Modellen.

## Befehle

- `/free` – Wechselt zu `openrouter/openrouter/free`
- `/premium` – Wechselt zu `openrouter/minimax/minimax-m2.5`
- `/auto` – Wechselt zu `openrouter/auto`
- `/model` – Zeigt aktuelle Modell-Infos (Anzahl Eintraege, Status)

## Funktionsweise

1. **Befehl ausfuehren**: `/free`, `/premium`, `/auto` oder `/model`
2. **Skript ausfuehren**: `scripts/switch.py` mit dem jeweiligen Parameter
3. **Wechsel**: ALLE Vorkommen von openrouter/* werden durch das Zielmodell ersetzt
4. **Status**: Die Anzahl der gefundenen und ersetzten Eintraege wird ausgegeben
5. **Gateway restart**: Automatisch versucht, den Gateway neu zu starten (falls notwendig)

### Hinweis

- Das Skript speichert ein Backup unter `~/.openclaw/openclaw.json.backup` vor jeder Aenderung.
- Fehlermeldungen werden im Chat angezeigt, falls der Gateway Neustart nicht moeglich ist.