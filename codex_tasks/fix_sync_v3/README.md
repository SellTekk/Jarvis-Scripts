# Codex Task Seed

Task:

WICHTIG: Ändere die EXISTIERENDE Datei 'bridge_main.py' im Root des Repos (nicht in codex_tasks/). 

In der Datei 'bridge_main.py' suche die Funktion 'get_open_prs' bei Zeile 559. Diese Funktion sucht nur PRs mit base=main:
`python
def get_open_prs(repo, base_branch='main'):
    result = github_request('GET', f'/repos/{repo}/pulls?state=open&base={base_branch}&sort=created&direction=desc')
`

Ändere diese Funktion so, dass sie AUCH PRs findet, wo baseBranch mit 'codex-' beginnt. 

Dann suche die sync() Funktion (Zeile 702) und ändere den Aufruf von get_open_prs() so, dass auch diese PRs gemergt werden.

Bearbeite und committe die Änderungen an bridge_main.py (nicht an codex_tasks/ Dateien).

## Goal
- Nice CLI calculator
- Add tests
- Improve error handling
