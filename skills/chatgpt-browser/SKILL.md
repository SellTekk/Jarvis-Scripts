---
name: chatgpt-browser
description: "Alternative Code-Generierung via ChatGPT im Browser. Verwende diesen Skill wenn: (1) Codex-Kontingent erschöpft ist, (2) Benutzer 'chatgpt', 'chat gpt', 'gpt' oder ähnliches sagt, (3) Codex nicht verfügbar ist. Nutze den OpenClaw Browser um mit ChatGPT Code zu generieren statt Codex."
---

# ChatGPT Browser Workflow

Alternative Workflow zur Codex-Bridge wenn Codex nicht verfügbar ist.

## Wann verwenden

- Codex-Kontingent erschöpft ist
- Benutzer explizit ChatGPT erwähnt
- Codex-Bridge nicht funktioniert

## Voraussetzungen

1. OpenClaw Browser ist eingerichtet
2. Benutzer ist bei ChatGPT eingeloggt (chat.openai.com)
3. Oder: Benutzer hat Zugangsdaten um sich einzuloggen

## Workflow

### Schritt 1: Browser starten
```
browser action=start profile=openclaw
```

### Schritt 2: Zu ChatGPT navigieren
```
browser action=navigate targetUrl=https://chat.openai.com
```

### Schritt 3: Snapshot machen um Login-Status zu prüfen
```
browser action=snapshot
```

### Schritt 4: Falls nicht eingeloggt
- Benutzer um Login bitten
- Oder: Eingabefelder ausfüllen (Email/Passwort)
- Dann weitermachen

### Schritt 5: Prompt eingeben
- In das Chat-Eingabefeld tippen
- Auf Absenden klicken
- Warten bis ChatGPT antwortet

### Schritt 6: Ergebnis kopieren
- Code aus der Antwort kopieren
- In lokale Datei speichern oder dem Benutzer geben

## Browser-Befehle Referenz

| Befehl | Beschreibung |
|--------|--------------|
| `browser action=start profile=openclaw` | Browser starten |
| `browser action=navigate targetUrl=URL` | Zu URL navigieren |
| `browser action=snapshot` | Aktuellen Stand erfassen |
| `browser action=act request={"kind": "type", "ref": "feld", "text": "text"}` | Text eingeben |
| `browser action=act request={"kind": "click", "ref": "button"}` | Klicken |

## Tipps

- Nutze `profile=openclaw` für zuverlässigen isolierten Browser
- Nutze `snapshot` mit `compact=true` für kleinere Ausgaben
- Bei Problemen: `browser action=start profile=chrome` versuchen

## Unterschied zu Codex

| Aspekt | Codex | ChatGPT Browser |
|--------|-------|-----------------|
| Automatisch | ✅ Ja | ❌ Manuell |
| GitHub-Integration | ✅ Direkt | ❌ Keine |
| Speed | ⚡ Schnell | 🐢 Langsamer |
| Kontingent | Limitiert | Login-basiert |