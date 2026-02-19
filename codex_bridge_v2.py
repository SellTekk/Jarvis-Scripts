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
import subprocess
try:
    import requests
except ImportError:
    requests = None
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
    'log_file': str(Path.home() / '.codex_bridge' / 'codex_bridge.log'),
    'status_file': str(Path.home() / '.codex_bridge' / 'codex_bridge_status.json'),
    'inbox_label': 'openclaw-task',
    'processed_label': 'codex-dispatched',
    'install_dir': str(Path.home() / '.codex_bridge'),
}


def _ensure_parent_dir(file_path):
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

def _write_text(path, content):
    _ensure_parent_dir(path)
    Path(path).write_text(content, encoding='utf-8')

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {msg}"
    print(line)
    try:
        _ensure_parent_dir(CONFIG['log_file'])
        with open(CONFIG['log_file'], 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass

def load_auth():
    # 1) Umgebungsvariablen bevorzugen (am stabilsten fuer Automatisierung)
    env_token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if env_token:
        CONFIG['github_token'] = env_token
        return True

    # 2) OpenClaw auth profile (Windows + Linux + macOS Pfade)
    auth_candidates = [
        Path(r'C:\Users\no\.openclaw\agents\main\agent\auth-profiles.json'),
        Path.home() / '.openclaw' / 'agents' / 'main' / 'agent' / 'auth-profiles.json'
    ]

    for auth_file in auth_candidates:
        try:
            with open(auth_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                token = data.get('profiles', {}).get('github:default', {}).get('key')
                if token and 'DEIN_GITHUB' not in token:
                    CONFIG['github_token'] = token
                    return True
        except:
            pass

    # 3) Fallback: gh CLI Token holen (wenn vorhanden)
    try:
        token = subprocess.check_output(
            ['gh', 'auth', 'token'],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        ).strip()
        if token:
            CONFIG['github_token'] = token
            return True
    except:
        pass

    return False

def _read_file_content(file_path):
    """Textinhalt robust einlesen. UTF-8 zuerst, dann Latin-1 Fallback."""
    try:
        return file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        try:
            return file_path.read_text(encoding='latin-1')
        except:
            return None

def _parse_wait_flag(args):
    """Steuert workflow-Warteverhalten via --no-wait oder --wait=<sekunden>."""
    wait = True
    for arg in args:
        if arg == '--no-wait':
            wait = False
        elif arg.startswith('--wait='):
            try:
                CONFIG['max_wait'] = int(arg.split('=', 1)[1])
            except ValueError:
                pass
    return wait

def _apply_runtime_config():
    """Erlaubt automatische Konfiguration ohne Codeaenderung."""
    poll = os.environ.get('CODEX_BRIDGE_POLL')
    max_wait = os.environ.get('CODEX_BRIDGE_MAX_WAIT')
    default_repo = os.environ.get('CODEX_BRIDGE_DEFAULT_REPO')
    inbox_label = os.environ.get('CODEX_BRIDGE_INBOX_LABEL')
    processed_label = os.environ.get('CODEX_BRIDGE_PROCESSED_LABEL')

    if poll and poll.isdigit():
        CONFIG['poll_interval'] = int(poll)
    if max_wait and max_wait.isdigit():
        CONFIG['max_wait'] = int(max_wait)
    if default_repo:
        CONFIG['default_repo'] = default_repo
    if inbox_label:
        CONFIG['inbox_label'] = inbox_label
    if processed_label:
        CONFIG['processed_label'] = processed_label

    if not CONFIG.get('github_token'):
        token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
        if token and 'DEIN_GITHUB' not in token:
            CONFIG['github_token'] = token


# ============ GITHUB API ============

def github(method, endpoint, data=None):
    if requests is None:
        return {'error': 'Python-Modul "requests" fehlt. Installiere mit: pip install requests'}
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
    created = github('POST', f'/repos/{repo}/git/refs', {
        'ref': f'refs/heads/{branch_name}',
        'sha': sha
    })
    if 'error' in created and 'Reference already exists' in created.get('details', ''):
        return {'status': 200, 'data': {'ref': f'refs/heads/{branch_name}', 'object': {'sha': sha}}}
    return created

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
                content = _read_file_content(file)
                if content is None:
                    results.append({'file': rel_path, 'ok': False, 'reason': 'decode_failed'})
                    continue
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

def get_open_inbox_issues(repo, label=None):
    """Liest offene Aufgaben-Issues aus der GitHub-Inbox."""
    target_label = label or CONFIG['inbox_label']
    endpoint = f'/repos/{repo}/issues?state=open&labels={target_label}&per_page=20&sort=created&direction=asc'
    result = github('GET', endpoint)
    if 'error' in result:
        return result

    items = result.get('data', [])
    issues = [item for item in items if 'pull_request' not in item]
    return {'status': 200, 'data': issues}

def add_issue_label(repo, issue_number, label):
    return github('POST', f'/repos/{repo}/issues/{issue_number}/labels', {'labels': [label]})

def comment_issue(repo, issue_number, body):
    return github('POST', f'/repos/{repo}/issues/{issue_number}/comments', {'body': body})

def process_inbox_issue(repo, issue):
    """Nimmt ein OpenClaw-Issue und erstellt automatisch eine Codex-Aufgabe."""
    issue_number = issue.get('number')
    title = issue.get('title', 'OpenClaw Task')
    body = issue.get('body') or ''

    task = f"{title}\n\n{body}".strip()
    if not task:
        task = f'Aufgabe aus Issue #{issue_number}'

    branch = f'codex-issue-{issue_number}-{int(time.time())}'
    log(f'[INBOX] Verarbeite Issue #{issue_number}: {title}')

    branch_result = create_branch(repo, branch)
    if 'error' in branch_result:
        return {'error': f"Branch konnte nicht erstellt werden: {branch_result.get('error')}"}

    issue_result = create_codex_issue(repo, branch, task)
    if 'error' in issue_result:
        return {'error': f"Codex-Issue konnte nicht erstellt werden: {issue_result.get('error')}"}

    codex_issue = issue_result.get('data', {})
    codex_url = codex_issue.get('html_url', 'unbekannt')
    codex_number = codex_issue.get('number', '?')

    add_issue_label(repo, issue_number, CONFIG['processed_label'])
    comment_issue(
        repo,
        issue_number,
        (
            '✅ Aufgabe wurde an Codex uebergeben.\n\n'
            f'- Branch: `{branch}`\n'
            f'- Codex-Issue: #{codex_number} ({codex_url})\n'
        )
    )

    return {
        'status': 'dispatched',
        'source_issue': issue_number,
        'branch': branch,
        'codex_issue_url': codex_url,
    }

def process_inbox(repo, once=True):
    """Automatische Aufgaben-Inbox: OpenClaw-Issues -> Codex-Issues."""
    processed = []

    while True:
        inbox = get_open_inbox_issues(repo)
        if 'error' in inbox:
            return inbox

        for issue in inbox.get('data', []):
            labels = [label.get('name') for label in issue.get('labels', [])]
            if CONFIG['processed_label'] in labels:
                continue

            result = process_inbox_issue(repo, issue)
            processed.append(result)

        if once:
            break

        log(f"[INBOX] Warten {CONFIG['poll_interval']}s auf neue Aufgaben...")
        time.sleep(CONFIG['poll_interval'])

    return {'status': 'ok', 'processed': processed, 'count': len(processed)}

def install_bridge(repo=None):
    """Installiert die Bridge fuer den autonomen OpenClaw->GitHub->Codex Workflow."""
    target_repo = repo or CONFIG['default_repo']
    install_dir = Path(CONFIG['install_dir'])
    install_dir.mkdir(parents=True, exist_ok=True)

    source = Path(__file__).resolve()
    target_script = install_dir / 'codex_bridge_v2.py'
    target_script.write_text(source.read_text(encoding='utf-8'), encoding='utf-8')

    env_example = f"""# Codex Bridge Autostart Config\nGITHUB_TOKEN=dein_github_token\nCODEX_BRIDGE_DEFAULT_REPO={target_repo}\nCODEX_BRIDGE_INBOX_LABEL={CONFIG['inbox_label']}\nCODEX_BRIDGE_PROCESSED_LABEL={CONFIG['processed_label']}\nCODEX_BRIDGE_POLL={CONFIG['poll_interval']}\n"""
    _write_text(str(install_dir / '.env.example'), env_example)

    linux_launcher = f"""#!/usr/bin/env bash\nset -euo pipefail\ncd \"{install_dir}\"\npython3 codex_bridge_v2.py inbox {target_repo} --daemon\n"""
    _write_text(str(install_dir / 'run_inbox.sh'), linux_launcher)
    os.chmod(install_dir / 'run_inbox.sh', 0o755)

    windows_launcher = f"""@echo off\ncd /d {install_dir}\npython codex_bridge_v2.py inbox {target_repo} --daemon\n"""
    _write_text(str(install_dir / 'run_inbox.bat'), windows_launcher)

    service = f"""[Unit]\nDescription=Codex Bridge Inbox Worker\nAfter=network.target\n\n[Service]\nType=simple\nWorkingDirectory={install_dir}\nExecStart=/usr/bin/python3 {install_dir / 'codex_bridge_v2.py'} inbox {target_repo} --daemon\nRestart=always\nRestartSec=5\n\n[Install]\nWantedBy=multi-user.target\n"""
    _write_text(str(install_dir / 'codex-bridge.service.example'), service)

    return {
        'status': 'installed',
        'install_dir': str(install_dir),
        'script': str(target_script),
        'repo': target_repo,
        'next_steps': [
            f'1) Token setzen: export GITHUB_TOKEN=... (oder in {install_dir}/.env)',
            f'2) Starten: {install_dir}/run_inbox.sh',
            f'3) Aufgaben per GitHub-Issue mit Label "{CONFIG["inbox_label"]}" anlegen'
        ]
    }

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
    _ensure_parent_dir(CONFIG['status_file'])
    with open(CONFIG['status_file'], 'w', encoding='utf-8') as f:
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
    _apply_runtime_config()
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'help'

    if cmd == 'install':
        repo = sys.argv[2] if len(sys.argv) > 2 else CONFIG['default_repo']
        print(json.dumps(install_bridge(repo), indent=2, default=str))
        sys.exit(0)

    if cmd == 'help':
        print("""
Codex Bridge v2 - OpenClaw -> GitHub -> Codex -> GitHub -> OpenClaw
====================================================================

Befehle:

  install [repo]                    Bridge lokal installieren (Autobetrieb vorbereiten)
  test                              GitHub Verbindung testen
  send <repo> "<task>" [ordner]     Code an Codex senden
  status <repo> <branch>            Codex Status pruefen
  result <repo> <branch>            Ergebnisse holen
  inbox [repo] [--daemon]           OpenClaw-Issues automatisch an Codex uebergeben
  workflow <repo> "<task>" [ordner] [--no-wait|--wait=sek]
                                    Kompletter Workflow (senden + warten + holen)

Automatisch:
  - Token wird aus GITHUB_TOKEN/GH_TOKEN, OpenClaw-Profil oder gh CLI geladen
  - Logs/Status werden unter ~/.codex_bridge gespeichert
  - Inbox-Modus: Label `openclaw-task` => automatische Uebergabe an Codex

Beispiele:

  python codex_bridge_v2.py install SellTekk/Jarvis-Scripts
  python codex_bridge_v2.py test
  python codex_bridge_v2.py inbox SellTekk/Jarvis-Scripts --daemon
        """)
        sys.exit(0)

    load_auth()
    if not CONFIG['github_token']:
        print("[ERROR] GitHub Token nicht gefunden!")
        sys.exit(1)

    if cmd == 'test':
        repos = github('GET', '/user/repos?per_page=5')
        if 'error' in repos:
            print(f"[ERROR] {repos['error']}")
        else:
            print("[OK] GitHub Connection!")
            for r in repos.get('data', []):
                print(f"  - {r['full_name']}")
    
    elif cmd == 'send' and len(sys.argv) > 2:
        repo = sys.argv[2]
        task = sys.argv[3] if len(sys.argv) > 3 else 'Automatischer Codex Task'
        folder = sys.argv[4] if len(sys.argv) > 4 and not sys.argv[4].startswith('--') else None
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

    elif cmd == 'inbox':
        repo = sys.argv[2] if len(sys.argv) > 2 else CONFIG['default_repo']
        daemon_mode = '--daemon' in sys.argv[3:]
        result = process_inbox(repo, once=not daemon_mode)
        print(json.dumps(result, indent=2, default=str))
    
    elif cmd == 'workflow' and len(sys.argv) > 2:
        repo = sys.argv[2]
        task = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else 'Automatischer Codex Task'
        folder = None
        if len(sys.argv) > 4 and not sys.argv[4].startswith('--'):
            folder = sys.argv[4]

        wait = _parse_wait_flag(sys.argv[4:])
        result = full_workflow(repo, task, folder, wait=wait)
        print(json.dumps(result, indent=2, default=str))
    
    else:
        print("[ERROR] Unbekannter Befehl. Nutze: python codex_bridge_v2.py help")
