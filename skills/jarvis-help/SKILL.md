---
name: jarvis-help
description: "Generiert strukturierte Help-Requests für ChatGPT wenn ich nicht weiterkomme. Trigger: (1) /help slash command, (2) Nach 3 fehlgeschlagenen retries, (3) Bei unbekannten Fehlern. Output: Copy-paste Template für ChatGPT."
---

# Jarvis-Help

Erstellt strukturierte Help-Requests für ChatGPT wenn ich nicht weiterkomme.

## Trigger (Wann aktivieren)

Aktiviere diesen Skill in diesen Situationen:
1. User sagt `/help`
2. Nach **3 fehlgeschlagenen Versuchen** den gleichen Fehler zu fixen
3. Bei **unbekannten Fehlern** die ich nicht googlen kann
4. Wenn ich keine Doku/Website finde die weiterhilft
5. Wenn ich den User fragen soll "Weißt du was das ist?"

## Workflow

1. **Problem erkennen** - Was ist der genaue Fehler?
2. **Was ich schon versucht habe** - Liste deine Debugging-Schritte
3. **User fragen:** "Brauchst du Hilfe?" mit fertigem Template
4. **Template zeigen** - Copy-paste für ChatGPT vorbereiten

## Template für ChatGPT

```
🤔 Brauche kurz Hilfe bei folgendem Problem:

**Fehlermeldung:**
[Hier den genauen Fehler eintragen]

**Kontext:**
- OS: [Windows/Linux/Mac]
- Tool: [OpenClaw/Browser/etc]
- Letzte Änderung: [Was wurde geändert?]

**Was ich schon versucht habe:**
1. [Versuch 1]
2. [Versuch 2]
3. [Versuch 3]

**Frage:**
[Was genau ich nicht verstehe oder brauche]

Kannst du mir helfen?
```

## Wichtig

- Erst **selbst versuchen** (googlen, docs lesen, debuggen)
- Erst wenn nix hilft → User fragen
- Niemals einfach aufgeben ohne Debugging
