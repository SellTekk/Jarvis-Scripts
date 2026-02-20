# Codex Task Seed

Task:

WICHTIG! Du musst die EXISTIERENDE Datei bridge_main.py im Root des Repos bearbeiten.

Der aktuelle Code in bridge_main.py (Zeile 559-563):
`python
def get_open_prs(repo, base_branch='main'):
    result = github_request('GET', f'/repos/{repo}/pulls?state=open&base={base_branch}&sort=created&direction=desc')
    if 'error' in result:
        return []
    return result.get('data', [])
`

Das Problem: Diese Funktion sucht nur PRs mit base=main. PR #4 hat base=codex-1771505258 und wird nicht gefunden.

Ändere die Funktion SO (ersetze die alten Zeilen):
`python
def get_open_prs(repo, base_branch='main'):
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

Committe die Änderungen an bridge_main.py.

## Goal
- Nice CLI calculator
- Add tests
- Improve error handling
