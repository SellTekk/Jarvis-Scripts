# Codex Task Seed

Task:

Ändere die Datei bridge_main.py im Root des Repos.

Suche die Funktion get_open_prs() (ca. Zeile 559) und ersetze sie durch:

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
