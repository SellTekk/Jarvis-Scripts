# Codex Task Seed

Task:

Entwickle ein Callback-System für die Codex-Bridge:

PROBLEM:
- Nach einem dispatch wartet der Agent NICHT auf das Ergebnis
- Der Cron-Job 'codex-sync' läuft alle 5 Minuten und merged PRs
- Der Agent weiß NICHT wann sein PR gemerged wurde
- Er kann seine Arbeit NICHT fortsetzen

LÖSUNGSANSATZ:
1. Beim dispatch die PR-Nummer und Session-ID speichern (in einer JSON-Datei oder ähnlich)
2. Der Cron-Job 'codex-sync' prüft nach dem Merge ob es einen Callback gibt
3. Bei erfolgreichem Merge: eine Callback-Nachricht senden (z.B. an Telegram oder die Session)
4. Die Nachricht sollte enthalten: PR-Nummer, Status, was als nächstes zu tun ist

AUFGABE:
- Analysiere die aktuelle bridge_main.py und den Cron-Job
- Erstelle einen Vorschlag für das Callback-System
- Der Code soll in bridge_main.py eingebaut werden
- Implementiere es wenn möglich

Zeige mir am Ende welche Änderungen du gemacht hast.

## Goal
- Nice CLI calculator
- Add tests
- Improve error handling
