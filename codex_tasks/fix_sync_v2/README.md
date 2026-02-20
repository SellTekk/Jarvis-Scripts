# Codex Task Seed

Task:

FIX THIS SPECIFIC CODE in bridge_main.py (lines 559-563):

Die Funktion get_open_prs() sucht nur nach PRs mit base=main:
`python
def get_open_prs(repo, base_branch='main'):
    result = github_request('GET', f'/repos/{repo}/pulls?state=open&base={base_branch}&sort=created&direction=desc')
`

Problem: PR #4 hat base=codex-1771505258, nicht main. Deshalb wird er nicht gefunden.

LÖSUNG: Ändere die Sync-Logik in der sync() Funktion (ab Zeile 702), damit sie AUCH PRs mit baseBranch findet, die mit 'codex-' beginnen. Die Funktion soll:
1. Erst PRs mit base=main suchen (wie bisher)
2. DANN auch PRs suchen, wo base mit 'codex-' beginnt (z.B. codex-1771505258)
3. Alle gefundenen PRs mergen

Zeige mir am Ende welche Änderungen du gemacht hast.

## Goal
- Nice CLI calculator
- Add tests
- Improve error handling
