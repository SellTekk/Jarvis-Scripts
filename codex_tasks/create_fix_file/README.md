# Codex Task Seed

Task:

Erstelle eine NEUE Datei 'bridge_main_sync_fix.py' im Root des Repos (neben bridge_main.py). 

Diese Datei soll eine verbesserte Version der sync-Logik enthalten:

1. Kopiere die Funktion get_open_prs() von bridge_main.py (Zeile 559)
2. Ändere sie so, dass sie AUCH PRs findet wo base mit 'codex-' beginnt
3. Erstelle eine verbesserte sync() Funktion die beide Arten von PRs merged

Der Code soll so aussehen:

`python
def get_all_codex_prs(repo):
    '''Findet alle offenen Codex-PRs (base=main ODER base=codex-*)'''
    all_prs = []
    
    # Suche PRs mit base=main
    prs_main = github_request('GET', f'/repos/{repo}/pulls?state=open&base=main')
    if isinstance(prs_main, dict) and 'data' in prs_main:
        all_prs.extend(prs_main['data'])
    
    # Suche PRs mit base=codex-*
    prs_codex = github_request('GET', f'/repos/{repo}/pulls?state=open&base=codex-')
    if isinstance(prs_codex, dict) and 'data' in prs_codex:
        all_prs.extend(prs_codex['data'])
    
    return all_prs
`

Committe diese neue Datei.

## Goal
- Nice CLI calculator
- Add tests
- Improve error handling
