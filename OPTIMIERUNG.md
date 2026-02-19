# Codex Bridge Optimierung

## Auftrag
Bitte optimiere die `codex_bridge_v2.py` Datei in diesem Branch:

1. **Bugs finden und fixen**
2. **Sicherheit verbessern** (Token-Handling, Input-Validation)
3. **Performance optimieren**
4. **Code-Qualität verbessern** (Lesbarkeit, Dokumentation)

## Wichtige Features die funktionieren müssen:
- `send` Command: Erstellt GitHub Issue mit @codex
- `inbox` Command: Verarbeitet Issues mit Label "openclaw-task" automatisch
- `install` Command: Installiert die Bridge in ~/.codex_bridge
- Closed Loop: OpenClaw -> GitHub -> Codex -> GitHub -> OpenClaw

## Bekannte Probleme die noch existieren könnten:
- Inbox erstellt manchmal doppelte @codex im Issue Body
- Kein PR wird automatisch erstellt

Bitte den Code analysieren und verbessern!