---
name: chatgpt-bridge
description: "Nutze ChatGPT für Code-Generierung, Debugging und Problemlösung. Verwende diesen Skill wenn: (1) Benutzer '/chatgptbridge' sagt, (2) Benutzer 'frag ChatGPT' oder 'mit ChatGPT' sagt, (3) Codex nicht verfügbar ist, (4) Benutzer Hilfe bei Code oder Projekten braucht. Dieser Skill nutzt den OpenClaw Browser um mit ChatGPT zu interagieren."
---

# ChatGPT Bridge

Nutze ChatGPT als Alternative zur Codex-Bridge für Code-Generierung und Debugging.

## Trigger

- `/chatgptbridge`
- "frag ChatGPT", "mit ChatGPT", "ChatGPT fragen"
- "schreib mir Code", "debugge das", "hilf mir mit..."

## Workflow

### Schritt 1: Anfrage klären
Falls der User nur `/chatgptbridge` sagt, frage nach: "Was brauchst du?"

### Schritt 2: Browser starten (falls nicht läuft)
```
browser action=start profile=openclaw
```

### Schritt 3: Zum OpenClaw Projekt navigieren
```
browser action=navigate targetUrl=https://chatgpt.com/g/g-p-69a13ee32b00819186ce4dbb700a1f84-openclaw/project
```

### Schritt 4: Snapshot machen um Input-Feld zu finden
```
browser action=snapshot compact=true
```

### Schritt 5: Prompt eingeben
- Finde das Chat-Eingabefeld
- Tippe die Anfrage des Users
- Klicke auf Absenden

### Schritt 6: Warten auf Antwort
- Warte bis ChatGPT geantwortet hat
- Mache regelmäßig snapshots um den Fortschritt zu sehen

### Schritt 7: Ergebnis verarbeiten
- Lese die Antwort aus dem snapshot
- Formatiere sie für den User
- Speichere ggf. Code in lokale Dateien

## Wichtige Hinweise

- Nutze `compact=true` bei snapshots für kürzere Ausgaben
- Der Browser läuft im `openclaw` Profil (isoliert)
- Das OpenClaw Projekt bei ChatGPT: https://chatgpt.com/g/g-p-69a13ee32b00819186ce4dbb700a1f84-openclaw/project
- Bei Problemen: Browser neu starten mit `browser action=start profile=openclaw`

## Beispiel-Prompt für ChatGPT

"Schreibe mir einen einfachen Python Taschenrechner mit den Grundrechenarten. Der Code soll gut lesbar sein und Funktionen für add, subtract, multiply, divide enthalten."

## Nach der Antwort

- Zeige die Antwort dem User
- Frage ob der Code gespeichert werden soll
- Falls ja, speichere ihn in eine Datei im Workspace