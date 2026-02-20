---
name: codex-bridge-main
description: "Closed-loop Bridge: OpenClaw -> GitHub -> Codex -> PR -> merge to main -> git pull -> OpenClaw."
---

# Codex Bridge (Main Routed)

Dieses Skill schließt den Kreis wirklich: OpenClaw -> GitHub -> Codex -> GitHub(PR) -> merge nach main -> OpenClaw pullt main

## Voraussetzungen (Windows)

1) Git installiert (Git for Windows)
2) Python 3 installiert (py launcher empfohlen)
3) GitHub Token gesetzt (User-Umgebungsvariable):
   - `setx GITHUB_TOKEN "ghp_...."`
   - oder `setx GH_TOKEN "ghp_...."`

Token braucht Rechte für:
- Issues erstellen (für @codex)
- PR merge (PUT /merge)
- Repo read (PRs listen)

## 1-Klick Installation

Doppelklick:
- `scripts\INSTALL (Doppelklick).cmd`

Das macht:
- Repo Clone nach `%USERPROFILE%\.openclaw\repos\Jarvis-Scripts`
- Junction/Link nach `%USERPROFILE%\.openclaw\skills\codex-bridge-auto` (Skill liegt im Repo unter openclaw_skills/codex-bridge-auto)
- Windows Task OpenClaw Codex Sync (alle 2 Minuten): merge Codex-PRs -> pull main

## Manuell testen (ohne Task)

1) Dispatch (branch + issue @codex):
```
py -3 scripts\bridge_main.py dispatch --repo SellTekk/Jarvis-Scripts --task "Baue Taschenrechner Projekt (Python) im Ordner codex_tasks/calculator" --local "%USERPROFILE%\.openclaw\repos\Jarvis-Scripts" --base main --route codex_tasks/calculator
```

2) Sync (PR mergen + pull main):
```
py -3 scripts\bridge_main.py sync --repo SellTekk/Jarvis-Scripts --local "%USERPROFILE%\.openclaw\repos\Jarvis-Scripts" --base main --merge --pull
```

Logs:
- `%USERPROFILE%\.openclaw\codex_bridge_main.log