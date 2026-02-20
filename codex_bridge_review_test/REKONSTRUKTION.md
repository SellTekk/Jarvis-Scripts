# Codex Bridge Final - Rekonstruktionsplan

**Backup Stand:** 2026-02-20
**Status:** ✅ Funktionsfähig

---

## Verzeichnis-Struktur

```
codex-bridge-final/
├── SKILL.md                 # Skill Definition
├── skill-meta.json          # Skill Metadaten
└── scripts/
    ├── bridge_main.py       # Hauptskript (dispatch + sync)
    ├── config.json          # Konfiguration
    ├── api_helpers.py       # GitHub API Helper
    └── push_helpers.py      # Git Push + API Fallback
```

---

## Wichtige Dateien

### 1. bridge_main.py
Das Herzstück mit folgenden Funktionen:
- `dispatch()` - Erstellt Branch, Seed Files, pushed, erstellt PR, @codex Comment
- `sync()` - Findet offene Codex PRs, merged sie, pullt lokal
- `gh_api()` - GitHub API Wrapper
- `create_pr()` - Erstellt Pull Request
- `comment_pr()` - Fügt Comment hinzu (triggert Codex)
- `merge_pr()` - Merged einen PR
- `_git_push_with_token()` - Non-interaktiver Git Push mit Token
- `api_push_changed_files()` - API Fallback wenn Git Push hängt
- `commit_push()` - Commit + Push mit Fallback

### 2. push_helpers.py
Enthält:
- `_git_push_with_token()` - Git Push mit Token in URL (verhindert UI Prompt)
- `api_push_changed_files()` - Fallback: Dateien per GitHub API hochladen

### 3. api_helpers.py
Enthält:
- `api_get_ref()` - Git Ref abrufen
- `api_create_branch()` - Branch erstellen
- `api_put_file()` - File per API hochladen

---

## Cron Job (WICHTIG!)

Der Sync läuft alle 2 Minuten als OpenClaw Cron Job.

### Job Konfiguration:
```json
{
  "name": "codex-sync",
  "schedule": {"kind": "every", "everyMs": 120000},
  "payload": {
    "kind": "agentTurn",
    "message": "Run codex sync: execute 'python C:\\Users\\no\\.openclaw\\skills\\codex-bridge-main\\scripts\\bridge_main.py sync --repo SellTekk/Jarvis-Scripts --local \"C:\\Users\\no\\.openclaw\\repos\\Jarvis-Scripts\" --base main --merge --pull' and report the result."
  },
  "sessionTarget": "isolated"
}
```

### Cron Job erstellen:
```bash
# 1. jobs.json reparieren (falls corrupted)
echo "{}" > C:\Users\no\.openclaw\cron\jobs.json

# 2. Cron Job hinzufügen (via OpenClaw)
# Oder alternativ als Windows Scheduled Task:
# python scripts\bridge_main.py sync --repo SellTekk/Jarvis-Scripts --local "%USERPROFILE%\.openclaw\repos\Jarvis-Scripts" --base main --merge --pull
```

---

## Workflow

### 1. Dispatch (Task an Codex senden)
```bash
python C:\Users\no\.openclaw\skills\codex-bridge-main\scripts\bridge_main.py dispatch --repo SellTekk/Jarvis-Scripts --local "C:\Users\no\.openclaw\repos\Jarvis-Scripts" --base main --task "Deine Aufgabe" --route dein/ordner
```

### 2. Sync (Automatisch alle 2 Minuten)
- Findet alle PRs mit Branch `codex-*`
- Merged sie nach main
- Pullt lokal

---

## Rekonstruktion (wenn kaputt)

### Schritt 1: Backup zurückkopieren
```powershell
Copy-Item -Path "C:\Users\no\Desktop\codex-bridge-final\*" -Destination "C:\Users\no\.openclaw\skills\codex-bridge-main\" -Recurse -Force
```

### Schritt 2: Cron Job erstellen
```powershell
# Via OpenClaw Gateway:
openclaw gateway restart  # falls nötig
# Dann cron job hinzufügen (siehe oben)
```

### Schritt 3: Testen
```bash
# Dispatch
python C:\Users\no\.openclaw\skills\codex-bridge-main\scripts\bridge_main.py dispatch --repo SellTekk/Jarvis-Scripts --local "C:\Users\no\.openclaw\repos\Jarvis-Scripts" --base main --task "Test" --route test123

# Manueller Sync
python C:\Users\no\.openclaw\skills\codex-bridge-main\scripts\bridge_main.py sync --repo SellTekk/Jarvis-Scripts --local "C:\Users\no\.openclaw\repos\Jarvis-Scripts" --base main --merge --pull
```

---

## Key Lessons / Was wir gelernt haben

1. **Git Push hängt auf Windows** - wegen Git Credential Manager UI Prompt
   - Lösung: Token in Remote URL einbetten + GIT_TERMINAL_PROMPT=0
   
2. **Codex triggern** - NICHT über Issues, sondern über PR Comments
   - `@codex` auf PR Comment triggert Codex Cloud Tasks
   
3. **Closed Loop** - Alles automatisch via Cron Job
   - Dispatch → Codex arbeitet → Sync merged → Pull

---

## Kontakte / Token

- GitHub Token: Als Umgebungsvariable `GITHUB_TOKEN` oder `GH_TOKEN`
- Repo: SellTekk/Jarvis-Scripts
- Local Repo: C:\Users\no\.openclaw\repos\Jarvis-Scripts

---

**Erstellt:** 2026-02-20 von Jarvis