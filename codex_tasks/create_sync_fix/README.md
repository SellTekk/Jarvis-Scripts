# Codex Task Seed

Task:

Erstelle eine NEUE Datei namens 'sync_fix.py' im ROOT des Repos (direkt neben bridge_main.py).

Diese Datei soll diese Funktion enthalten:

`python
# sync_fix.py - Erweitert bridge_main.py um codex-* PR Support

def get_open_prs_enhanced(repo):
    '''Findet alle offenen PRs für base=main UND base=codex-*'''
    all_prs = []
    
    # PRs mit base=main
    result_main = github_request('GET', f'/repos/{repo}/pulls?state=open&base=main')
    if 'error' not in result_main:
        all_prs.extend(result_main.get('data', []))
    
    # PRs mit base=codex-*
    result_codex = github_request('GET', f'/repos/{repo}/pulls?state=open&base=codex-')
    if 'error' not in result_codex:
        all_prs.extend(result_codex.get('data', []))
    
    return all_prs
`

Erstelle die Datei sync_fix.py im Root (nicht in codex_tasks/). Committe sie.

## Goal
- Nice CLI calculator
- Add tests
- Improve error handling
