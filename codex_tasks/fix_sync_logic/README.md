# Codex Task Seed

Task:

Analysiere und fixe die bridge_main.py Sync-Logik: Die get_open_prs() Funktion findet nur PRs wo base=main, aber es gibt einen offenen PR (#4) mit base=codex-1771505258. Der Sync findet deshalb 0 PRs. Lösung: Entweder die Sync-Logik anpassen um auch PRs mit codex-* base zu finden, oder den Workflow so ändern dass CodeX immer nach main merged.

## Goal
- Nice CLI calculator
- Add tests
- Improve error handling
