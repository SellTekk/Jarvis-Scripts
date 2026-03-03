# Crawler Fix: `crawler_handy.py` SIGKILL-Robustheit

## Analyse des bestehenden Scripts

`crawler_handy.py` ist bereits **teilweise restart-fähig**, weil:

- Ergebnisse nach **jedem Produkt** sofort in die Output-Excel geschrieben werden.
- Beim nächsten Start wird die Output-Datei eingelesen und bereits verarbeitete SKUs übersprungen.

Das ist eine gute Basis bei Windows-Kills (z. B. alle 20–30 Minuten), aber es fehlt:

1. Ein externer Watchdog, der den Prozess automatisch wieder startet.
2. Eine explizite Checkpoint-Datei für Laufstatus (Restarts, Fortschritt, letzter Exit-Code).

## Neue Lösung

Neu hinzugefügt: `crawler_handy_wrapper.py`

Der Wrapper:

- startet `crawler_handy.py` als Subprozess,
- erkennt abnormalen Exit (Exit-Code ungleich 0),
- liest den Fortschritt aus der Output-Datei,
- schreibt/aktualisiert `crawler_handy.checkpoint.json`,
- startet den Crawler neu, bis alle Produkte verarbeitet sind.

## Start

```bash
python codex_tasks/crawler_fix/crawler_handy_wrapper.py
```

## Checkpoint

Datei: `codex_tasks/crawler_fix/crawler_handy.checkpoint.json`

Beispielinhalte:

- `restart_count`
- `last_processed`
- `total_products`
- `remaining`
- `last_exit_code`
- `completed`

Damit ist der Laufzustand auch zwischen Wrapper-Neustarts transparent.
