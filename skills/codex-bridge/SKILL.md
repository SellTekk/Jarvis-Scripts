---
name: codex-bridge
description: "OpenClaw Codex Bridge: Sende Tasks an GitHub Codex, prüfe Status, hole Ergebnisse. Trigger: /codex, 'mit codex', 'codex bridge', 'codex send', 'codex test', 'codex status', 'codex result', 'codex workflow', 'an codex senden', 'delegiere an codex'."
---

# OpenClaw Codex Bridge

## ⚠️ DIESE BRIDGE EXISTIERT UND FUNKTIONIERT — NICHTS NEU BAUEN!

Letzter erfolgreicher Test: 2026-02-20 (PR #58 erstellt, gemerged, lokal gepullt)

---

## ⚠️ WAS DU NICHT TUN MUSST (WICHTIG!)

**Du brauchst NICHT manuell zu warten oder sync/merge aufzurufen!**

- ❌ NICHT manuell `bridge_main.py sync` ausführen
- ❌ NICHT auf Ergebnisse warten oder pollen
- ❌ NICHT nach dem Dispatch prüfen ob PR gemerged ist

**Alles passiert AUTOMATISCH:**

1. Task dispatchen → Codex arbeitet
2. Cron-Job "codex-sync" (alle 5 Min) → merged automatisch
3. Du wirst automatisch informiert wenn etwas passiert

**Dein Job nach dem Dispatch:**
- Task senden ✓
- Dann vergessen ✓
- Der Cron-Job erledigt den Rest automatisch

---

## Was macht die Bridge?

```
OpenClaw Agent → GitHub Branch+PR → Codex Cloud bearbeitet → PR gemerged → Lokal gepullt → Agent informiert User
```

Der gesamte Prozess läuft automatisch. Der Agent dispatcht eine Aufgabe, die Bridge erstellt einen Branch und PR auf GitHub, Codex Cloud bearbeitet die Aufgabe, und ein Cron-Job merged fertige PRs alle 5 Minuten und pullt die Änderungen lokal.

---

## Dateien & Pfade

| Was | Wo |
|---|---|
| Bridge v2 (test/send/status/result/workflow) | `C:\Users\no\.openclaw\workspace\codex_bridge_v2.py` |
| Bridge Main (dispatch/sync) | `C:\Users\no\.openclaw\skills\codex-bridge-main\scripts\bridge_main.py` |
| Lokales Repo | `C:\Users\no\.openclaw\repos\Jarvis-Scripts` |
| Default Repo | `SellTekk/Jarvis-Scripts` |
| Windows Launcher | `C:\Users\no\.openclaw\workspace\start_codex_bridge_win.bat` |
| Dieser Skill | `C:\Users\no\.openclaw\skills\codex-bridge\SKILL.md` |

---

## Befehle

### 1. GitHub-Verbindung testen
```powershell
cd C:\Users\no\.openclaw\workspace; py -3 codex_bridge_v2.py test
```
Erwartete Ausgabe: `[OK] GitHub Connection!` + Liste der Repos

### 2. Task an Codex senden (Dispatch)
```powershell
cd C:\Users\no\.openclaw\skills\codex-bridge-main\scripts; py -3 bridge_main.py dispatch --repo SellTekk/Jarvis-Scripts --task "DEINE AUFGABE" --local "C:\Users\no\.openclaw\repos\Jarvis-Scripts" --base main --route codex_tasks/ORDNERNAME
```
- Erstellt Branch, Seed-Dateien, PR und Issue mit @codex
- `--route` muss ein **neuer, einzigartiger** Ordnername sein (sonst "Nothing to commit")
- Ausgabe enthält PR-URL und Branch-Name

### 3. Sync (PRs mergen + lokal pullen)
```powershell
cd C:\Users\no\.openclaw\skills\codex-bridge-main\scripts; py -3 bridge_main.py sync --repo SellTekk/Jarvis-Scripts --local C:\Users\no\.openclaw\repos\Jarvis-Scripts --base main --merge --pull
```
- Findet offene Codex-PRs, merged sie, pullt main lokal
- **Läuft automatisch alle 5 Minuten via Cron-Job "codex-sync"**

### 4. Task senden via Bridge v2 (Alternative)
```powershell
cd C:\Users\no\.openclaw\workspace; py -3 codex_bridge_v2.py send SellTekk/Jarvis-Scripts "DEINE AUFGABE"
```

### 5. Status prüfen via Bridge v2
```powershell
cd C:\Users\no\.openclaw\workspace; py -3 codex_bridge_v2.py status SellTekk/Jarvis-Scripts BRANCHNAME
```

### 6. Ergebnis holen via Bridge v2
```powershell
cd C:\Users\no\.openclaw\workspace; py -3 codex_bridge_v2.py result SellTekk/Jarvis-Scripts BRANCHNAME
```

### 7. Kompletter Workflow (senden + warten + Ergebnis)
```powershell
cd C:\Users\no\.openclaw\workspace; py -3 codex_bridge_v2.py workflow SellTekk/Jarvis-Scripts "DEINE AUFGABE"
```

---

## Automatischer Sync (Cron-Job)

- **Name:** codex-sync
- **Intervall:** Alle 5 Minuten (300.000ms)
- **Was er tut:** Offene Codex-PRs finden → mergen → main lokal pullen
- **Status:** Aktiv, funktioniert (letzte Prüfung: 2026-02-20)

Der Cron-Job führt automatisch den Sync-Befehl aus. Du musst nichts manuell tun — neue PRs werden automatisch gemerged und lokal aktualisiert.

---

## Trigger-Wörter (DE + EN)

Wenn ein User eines dieser Wörter sagt, nutze diesen Skill:

```
/codex, codex bridge, codex test, codex send, codex status, codex result,
codex workflow, mit codex, an codex senden, delegiere an codex,
mach codex stuff, erstelle code, dispatch codex task, github codex,
send to codex, codex aufgabe, codex task, codex ergebnis, codex prüfen,
check codex, run codex, start codex, codex starten, codex ausführen
```

---

## Kompletter Workflow-Ablauf

```
1. User: "/codex Analysiere die OpenClaw Config"
   ↓
2. Agent liest diesen SKILL.md
   ↓
3. Agent führt dispatch aus:
   cd C:\Users\no\.openclaw\skills\codex-bridge-main\scripts
   py -3 bridge_main.py dispatch --repo SellTekk/Jarvis-Scripts \
     --task "Analysiere die OpenClaw Config" \
     --local "C:\Users\no\.openclaw\repos\Jarvis-Scripts" \
     --base main --route codex_tasks/analyse_config
   ↓
4. Bridge erstellt Branch + PR + Issue mit @codex auf GitHub
   ↓
5. Codex Cloud bearbeitet die Aufgabe im Branch
   ↓
6. Cron-Job "codex-sync" merged den fertigen PR (alle 5 Min)
   ↓
7. Lokales Repo wird aktualisiert
   ↓
8. Agent informiert User: "Codex hat PR #XX gemerged, Ergebnis liegt vor"
```

---

## Wichtige Hinweise

- **PowerShell:** Benutze `;` (Semikolon) statt `&&` zum Verketten von Befehlen
- **Pfade:** Immer volle Pfade verwenden, NICHT `~` oder relative Pfade
- **Route-Name:** Muss bei jedem Dispatch einzigartig sein, sonst schlägt der PR fehl
- **Token:** GitHub-Token wird aus `GITHUB_TOKEN` Env-Var oder OpenClaw `auth-profiles.json` geladen
- **Python:** `py -3` auf Windows, `python3` auf Linux/macOS

---

## Bekannte Probleme & Lösungen

| Problem | Lösung |
|---|---|
| "Nothing to commit" | Route-Name existiert schon → neuen Namen wählen |
| "PR create failed: 422" | Branch hat keine neuen Commits → Route-Name ändern |
| "issue: error" | Issue-Erstellung schlägt fehl → Codex wird trotzdem über PR getriggert |
| Git push hängt | Token-basierte Remote URL nutzen (bereits gefixt) |
| PowerShell `&&` Fehler | `;` statt `&&` verwenden |
| `~` wird nicht aufgelöst | Volle Pfade nutzen: `C:\Users\no\.openclaw\...` |
