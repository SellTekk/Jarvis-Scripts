#!/usr/bin/env python3
"""
OpenClaw Codex Bridge v2 - Vollautomatischer Workflow
======================================================
OpenClaw -> GitHub -> Codex Cloud -> GitHub -> OpenClaw

Workflow:
1. Agent erkennt "mit Codex" Befehl
2. Erstellt Branch + pusht Code nach GitHub
3. Erstellt Issue mit @codex Tag -> Codex Cloud arbeitet
4. Pollt auf Aenderungen (Commits/PR)
5. Liest Ergebnisse zurueck und liefert an User

Nutzung:
    python codex_bridge_v2.py send <repo> "<task>" [lokaler_ordner]
    python codex_bridge_v2.py status <repo> <branch>
    python codex_bridge_v2.py result <repo> <branch>
    python codex_bridge_v2.py test
"""

import os
import sys
import json
import base64
import time
import shutil
import subprocess
import requests
from pathlib import Path
from datetime import datetime

# ============ CONFIG ============

CONFIG = {
    'github_token': None,
    'github_user': 'SellTekk',
    'default_repo': 'SellTekk/Jarvis-Scripts',
    'default_branch': 'main',
    'poll_interval': 30,
    'max_wait': 600,
    'log_file': r'C:\Users\no\Desktop\codex_bridge_log.txt',
}

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(CONFIG['log_file'], 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass

def load_auth():
    auth_file = r'C:\Users\no\.openclaw\agents\main\agent\auth-profiles.json'
    try:
        with open(auth_file, 'r') as f:
            data = json.load(f)
            token = data.get('profiles', {}).get('github:default', {}).get('key')
            if token and 'DEIN_GITHUB' not in token:
                CONFIG['github_token'] = token
                return True
    except:
        pass
    return False

# ============ GITHUB API ============

def github(method, endpoint, data=None):
    if not CONFIG['github_token']:
        return {'error': 'GitHub Token fehlt'}
    url = f'https://api.github.com{endpoint}'
    headers = {
        'Authorization': f'token {CONFIG["github_token"]}',
        'Accept': 'application/vnd.github.v3+json'
    }
    try:
        r = requests.request(method, url, headers=headers, json=data)
        if r.status_code < 400:
            return {'status': r.status_code, 'data': r.json()}
        else:
            return {'error': f'HTTP {r.status_code}', 'details': r.text[:300]}
    except Exception as e:
        return {'error': str(e)}

def get_default_branch(repo):
    result = github('GET', f'/repos/{repo}')
    if 'error' in result:
        return 'main'
    return result.get('data', {}).get('default_branch', 'main')

def create_branch(repo, branch_name, base_branch=None):
    if not base_branch:
        base_branch = get_default_branch(repo)
    ref_result = github('GET', f'/repos/{repo}/git/ref/heads/{base_branch}')
    if 'error' in ref_result:
        return ref_result
    sha = ref_result.get('data', {}).get('object', {}).get('sha')
    if not sha:
        return {'error': 'SHA nicht gefunden'}
    return github('POST', f'/repos/{repo}/git/refs', {
        'ref': f'refs/heads/{branch_name}',
        'sha': sha
    })

def push_file(repo, branch, filepath, content, commit_msg):
    encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    existing = github('GET', f'/repos/{repo}/contents/{filepath}?ref={branch}')
    sha = existing.get('data', {}).get('sha') if existing.get('status') == 200 else None
    data = {'message': commit_msg, 'content': encoded, 'branch': branch}
    if sha:
        data['sha'] = sha
    return github('PUT', f'/repos/{repo}/contents/{filepath}', data)

def push_local_folder(repo, branch, local_path, commit_msg):
    """Pusht alle Dateien aus einem lokalen Ordner nach GitHub"""
    results = []
    local_path = Path(local_path)
    
    code_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', 
                       '.json', '.md', '.txt', '.sh', '.bat', '.sql', '.yaml', '.yml',
                       '.php', '.xml', '.toml', '.cfg', '.ini', '.env']
    
    for file in local_path.rglob('*'):
        if file.is_file() and file.suffix.lower() in code_extensions:
            rel_path = file.relative_to(local_path).as_posix()
            try:
                content = file.read_text(encoding='utf-8')
                result = push_file(repo, branch, rel_path, content, commit_msg)
                results.append({'file': rel_path, 'ok': 'error' not in result})
                log(f"  Pushed: {rel_path}")
            except:
                results.append({'file': rel_path, 'ok': False})
    
    return results

def create_codex_issue(repo, branch, task):
    """Erstellt ein GitHub Issue das Codex triggert"""
    body = f"""## Codex Aufgabe

**Task:** {task}

**Branch:** `{branch}`

**Anweisungen:**
- Arbeite im Branch `{branch}`
- Erstelle einen Pull Request wenn fertig
- Achte auf sauberen, funktionierenden Code

@codex Bitte erledige diese Aufgabe im Branch `{branch}`!
"""
    result = github('POST', f'/repos/{repo}/issues', {
        'title': f'[Codex] {task[:80]}',
        'body': body,
        'labels': ['codex', 'automation']
    })
    return result

def check_for_changes(repo, branch, base_branch=None):
    """Prueft ob Codex Aenderungen gemacht hat"""
    if not base_branch:
        base_branch = get_default_branch(repo)
    
    result = github('GET', f'/repos/{repo}/compare/{base_branch}...{branch}')
    if 'error' in result:
        return result
    
    data = result.get('data', {})
    return {
        'status': data.get('status', 'unknown'),
        'ahead_by': data.get('ahead_by', 0),
        'behind_by': data.get('behind_by', 0),
        'total_commits': data.get('total_commits', 0),
        'files_changed': len(data.get('files', [])),
        'files': [f.get('filename') for f in data.get('files', [])]
    }

def check_for_pr(repo, branch):
    """Prueft ob es einen PR fuer diesen Branch gibt"""
    owner = repo.split('/')[0]
    result = github('GET', f'/repos/{repo}/pulls?head={owner}:{branch}&state=open')
    if 'error' in result:
        return result
    
    prs = result.get('data', [])
    if prs:
        pr = prs[0]
        return {
            'found': True,
            'number': pr.get('number'),
            'title': pr.get('title'),
            'url': pr.get('html_url'),
            'state': pr.get('state'),
            'mergeable': pr.get('mergeable')
        }
    return {'found': False}

def read_file_from_branch(repo, filepath, branch):
    """Liest eine Datei aus einem bestimmten Branch"""
    result = github('GET', f'/repos/{repo}/contents/{filepath}?ref={branch}')
    if 'error' in result:
        return result
    try:
        content = base64.b64decode(result['data'].get('content', '')).decode('utf-8')
        return {'content': content, 'path': filepath}
    except:
        return {'error': 'Decode fehlgeschlagen'}

def get_all_files_from_branch(repo, branch, path=''):
    """Liest alle Dateien aus einem Branch"""
    result = github('GET', f'/repos/{repo}/contents/{path}?ref={branch}')
    if 'error' in result:
        return result
    
    items = result.get('data', [])
    if not isinstance(items, list):
        items = [items]
    
    files = {}
    for item in items:
        if item['type'] == 'file':
            file_content = read_file_from_branch(repo, item['path'], branch)
            if 'content' in file_content:
                files[item['path']] = file_content['content']
        elif item['type'] == 'dir':
            sub_files = get_all_files_from_branch(repo, branch, item['path'])
            if isinstance(sub_files, dict) and 'error' not in sub_files:
                files.update(sub_files)
    
    return files

# ============ WORKFLOWS ============

def send_to_codex(repo, task, local_folder=None):
    """
    SCHRITT 1: Code an Codex senden
    - Branch erstellen
    - Code pushen (optional)
    - Issue erstellen mit @codex
    """
    log("=" * 50)
    log("[START] CODEX BRIDGE - Code senden")
    log(f"  Repo: {repo}")
    log(f"  Task: {task}")
    log(f"  Lokal: {local_folder or 'keiner'}")
    
    # Branch erstellen
    branch = f"codex-{int(time.time())}"
    log(f"  Branch erstellen: {branch}")
    
    br = create_branch(repo, branch)
    if 'error' in br:
        log(f"  [ERROR] Branch: {br['error']}")
        return {'error': br['error']}
    log(f"  [OK] Branch erstellt")
    
    # Code pushen wenn lokaler Ordner angegeben
    if local_folder and os.path.exists(local_folder):
        log(f"  Code pushen aus: {local_folder}")
        push_results = push_local_folder(repo, branch, local_folder, f"Codex Task: {task}")
        pushed = sum(1 for r in push_results if r['ok'])
        log(f"  [OK] {pushed}/{len(push_results)} Dateien gepusht")
    
    # Task-Beschreibung als README in den Branch
    task_readme = f"# Codex Task\n\n{task}\n\nBranch: {branch}\nErstellt: {datetime.now()}\n"
    push_file(repo, branch, 'CODEX_TASK.md', task_readme, f"Codex Task: {task}")
    
    # Issue erstellen mit @codex
    log(f"  Issue erstellen mit @codex...")
    issue = create_codex_issue(repo, branch, task)
    if 'error' in issue:
        log(f"  [WARN] Issue: {issue['error']}")
        issue_url = 'nicht erstellt'
    else:
        issue_url = issue.get('data', {}).get('html_url', 'unbekannt')
        log(f"  [OK] Issue: {issue_url}")
    
    result = {
        'status': 'sent',
        'repo': repo,
        'branch': branch,
        'task': task,
        'issue_url': issue_url,
        'github_url': f'https://github.com/{repo}/tree/{branch}',
        'codex_url': 'https://chatgpt.com/codex'
    }
    
    log(f"  [DONE] Code gesendet!")
    log(f"  GitHub: {result['github_url']}")
    log(f"  Codex:  {result['codex_url']}")
    log("=" * 50)
    
    # Status-Datei schreiben
    status_file = r'C:\Users\no\Desktop\codex_bridge_status.json'
    with open(status_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    return result

def check_codex_status(repo, branch):
    """
    SCHRITT 2: Codex Status pruefen
    - Hat Codex Aenderungen gemacht?
    - Gibt es einen PR?
    """
    log("=" * 50)
    log("[CHECK] CODEX STATUS")
    log(f"  Repo: {repo}")
    log(f"  Branch: {branch}")
    
    # Aenderungen pruefen
    changes = check_for_changes(repo, branch)
    log(f"  Commits: {changes.get('total_commits', 0)}")
    log(f"  Dateien geaendert: {changes.get('files_changed', 0)}")
    
    # PR pruefen
    pr = check_for_pr(repo, branch)
    if pr.get('found'):
        log(f"  [OK] PR gefunden: {pr.get('url')}")
    else:
        log(f"  [WAIT] Noch kein PR")
    
    result = {
        'changes': changes,
        'pr': pr,
        'codex_done': changes.get('total_commits', 0) > 1 or pr.get('found', False)
    }
    
    log("=" * 50)
    return result

def get_codex_result(repo, branch):
    """
    SCHRITT 3: Ergebnisse holen
    - Alle Dateien aus dem Branch lesen
    - Diff anzeigen
    """
    log("=" * 50)
    log("[RESULT] CODEX ERGEBNISSE")
    log(f"  Repo: {repo}")
    log(f"  Branch: {branch}")
    
    # Alle Dateien holen
    files = get_all_files_from_branch(repo, branch)
    if isinstance(files, dict) and 'error' not in files:
        log(f"  [OK] {len(files)} Dateien gelesen")
        
        # Diff holen
        changes = check_for_changes(repo, branch)
        
        result = {
            'files': files,
            'changes': changes,
            'file_list': list(files.keys())
        }
        
        log(f"  Geaenderte Dateien: {changes.get('files', [])}")
        log("=" * 50)
        return result
    else:
        log(f"  [ERROR] Konnte Dateien nicht lesen")
        return {'error': 'Konnte Dateien nicht lesen', 'details': files}

def full_workflow(repo, task, local_folder=None, wait=True):
    """
    KOMPLETTER WORKFLOW:
    1. Senden
    2. Warten (optional)
    3. Ergebnis holen
    """
    log("\n" + "#" * 60)
    log("# CODEX BRIDGE - VOLLSTAENDIGER WORKFLOW")
    log("#" * 60)
    
    # 1. Senden
    send_result = send_to_codex(repo, task, local_folder)
    if 'error' in send_result:
        return send_result
    
    branch = send_result['branch']
    
    if not wait:
        return send_result
    
    # 2. Warten auf Codex
    log(f"\n[WAIT] Warte auf Codex (max {CONFIG['max_wait']}s)...")
    start = time.time()
    
    while time.time() - start < CONFIG['max_wait']:
        status = check_codex_status(repo, branch)
        
        if status.get('codex_done'):
            log("[OK] Codex hat gearbeitet!")
            
            # 3. Ergebnis holen
            result = get_codex_result(repo, branch)
            result['send'] = send_result
            result['status'] = 'completed'
            return result
        
        remaining = int(CONFIG['max_wait'] - (time.time() - start))
        log(f"  Noch {remaining}s... (naechster Check in {CONFIG['poll_interval']}s)")
        time.sleep(CONFIG['poll_interval'])
    
    log("[TIMEOUT] Codex hat nicht rechtzeitig geantwortet")
    return {
        'status': 'timeout',
        'send': send_result,
        'message': f'Codex hat innerhalb von {CONFIG["max_wait"]}s nicht geantwortet.',
        'next_steps': [
            f'Pruefe: https://chatgpt.com/codex',
            f'Pruefe: https://github.com/{repo}/tree/{branch}',
            f'Status: python codex_bridge_v2.py status {repo} {branch}',
            f'Ergebnis: python codex_bridge_v2.py result {repo} {branch}'
        ]
    }

# ============ CLI ============

if __name__ == '__main__':
    load_auth()
    
    if not CONFIG['github_token']:
        print("[ERROR] GitHub Token nicht gefunden!")
        sys.exit(1)
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'help'
    
    if cmd == 'test':
        repos = github('GET', '/user/repos?per_page=5')
        if 'error' in repos:
            print(f"[ERROR] {repos['error']}")
        else:
            print("[OK] GitHub Connection!")
            for r in repos.get('data', []):
                print(f"  - {r['full_name']}")
    
    elif cmd == 'send' and len(sys.argv) > 3:
        repo = sys.argv[2]
        task = sys.argv[3]
        folder = sys.argv[4] if len(sys.argv) > 4 else None
        result = send_to_codex(repo, task, folder)
        print(json.dumps(result, indent=2, default=str))
    
    elif cmd == 'status' and len(sys.argv) > 3:
        repo = sys.argv[2]
        branch = sys.argv[3]
        result = check_codex_status(repo, branch)
        print(json.dumps(result, indent=2, default=str))
    
    elif cmd == 'result' and len(sys.argv) > 3:
        repo = sys.argv[2]
        branch = sys.argv[3]
        result = get_codex_result(repo, branch)
        # Nur Dateiliste und Changes anzeigen (nicht den ganzen Code)
        display = {
            'file_list': result.get('file_list', []),
            'changes': result.get('changes', {})
        }
        print(json.dumps(display, indent=2, default=str))
    
    elif cmd == 'workflow' and len(sys.argv) > 3:
        repo = sys.argv[2]
        task = sys.argv[3]
        folder = sys.argv[4] if len(sys.argv) > 4 else None
        result = full_workflow(repo, task, folder, wait=True)
        print(json.dumps(result, indent=2, default=str))
    
    elif cmd == 'help':
        print("""
Codex Bridge v2 - OpenClaw -> GitHub -> Codex -> GitHub -> OpenClaw
====================================================================

Befehle:

  test                              GitHub Verbindung testen
  send <repo> "<task>" [ordner]     Code an Codex senden
  status <repo> <branch>            Codex Status pruefen
  result <repo> <branch>            Ergebnisse holen
  workflow <repo> "<task>" [ordner]  Kompletter Workflow (senden + warten + holen)

Beispiele:

  python codex_bridge_v2.py test
  python codex_bridge_v2.py send SellTekk/Jarvis-Scripts "Todo-Liste programmieren"
  python codex_bridge_v2.py send SellTekk/Jarvis-Scripts "Bug fixen" C:\\MeinProjekt
  python codex_bridge_v2.py status SellTekk/Jarvis-Scripts codex-1740012345
  python codex_bridge_v2.py result SellTekk/Jarvis-Scripts codex-1740012345
  python codex_bridge_v2.py workflow SellTekk/Jarvis-Scripts "Hello World"
        """)
    
    else:
        print("[ERROR] Unbekannter Befehl. Nutze: python codex_bridge_v2.py help")