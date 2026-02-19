# Codex Bridge V2 - OpenClaw Skill

## Übersicht

Dieser Skill ermöglicht es Allen OpenClaw Agents, den vollautomatischen Codex-Workflow zu nutzen:

```
Agent → GitHub → Codex Cloud → GitHub → OpenClaw → User
```

## Befehle

### Testen
```
codex test
```
Testet die GitHub-Verbindung.

### Senden (ohne Warten)
```
codex send <repo> "<task>" [ordner]
```
Erstellt Branch, pusht Code, erstellt Issue mit @codex.

### Status prüfen
```
codex status <repo> <branch>
```
Prüft ob Codex gearbeitet hat und ob PR existiert.

### Ergebnis holen
```
codex result <repo> <branch>
```
Liest die geänderten Dateien aus dem Branch.

### Vollständiger Workflow (Senden + Warten + Ergebnis)
```
codex workflow <repo> "<task>" [ordner]
```
Komplettlauf: Branch erstellen → Code pushen → Issue → Warten auf PR → Ergebnisse holen.

## Standard-Repo

- **Default:** SellTekk/Jarvis-Scripts
- Kann in jedem Befehl überschrieben werden

## Beispiele

```
codex test
codex send SellTekk/Jarvis-Scripts "Todo-Liste programmieren"
codex workflow SellTekk/Jarvis-Scripts "Bug im Login fixen"
codex status SellTekk/Jarvis-Scripts codex-1771501786
codex result SellTekk/Jarvis-Scripts codex-1771501786
```

## Für Agenten

Dieser Skill kann vonallen OpenClaw Agents genutzt werden. Der Agent erkennt "mit Codex" oder "/codex" Befehle und führt den entsprechenden Workflow aus.

## Technische Details

- Script: C:\Users\no\Desktop\codex_bridge_v2.py
- Log: C:\Users\no\Desktop\codex_bridge_log.txt
- Status: C:\Users\no\Desktop\codex_bridge_status.json