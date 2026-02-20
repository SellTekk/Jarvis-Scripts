#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bridge_main.py ==============
Closed-loop Bridge (main routed):
- dispatch: create branch from base, seed files into a repo route, open issue with @codex
- sync: find Codex PRs targeting base (default main) -> merge -> pull base locally

Token: setx GITHUB_TOKEN "ghp_..." (or GH_TOKEN)
"""

import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from urllib.parse import quote
from urllib import request, error

LOG_PATH = Path.home() / ".openclaw" / "codex_bridge_main.log"

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def load_token():
    tok = (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
    if tok:
        return tok
    
    # fallback: OpenClaw auth profile if exists
    candidates = [
        Path.home() / ".openclaw" / "agents" / "main" / "agent" / "auth-profiles.json",
        Path(r"C:\Users\no\.openclaw\agents\main\agent\auth-profiles.json"),
    ]
    for p in candidates:
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                t = (data.get("profiles", {}).get("github:default", {}) or {}).get("key", "")
                t = (t or "").strip()
                if t and "DEIN_GITHUB" not in t:
                    return t
        except Exception:
            pass
    return ""

def gh_api(method, path, token, body=None):
    url = "https://api.github.com" + path
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "openclaw-codex-bridge-main",
    }
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return resp.status, json.loads(raw) if raw else {}
    except error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"message": raw[:500]}
    except Exception as e:
        return 0, {"message": str(e)}


def api_get_ref(repo: str, token: str, branch: str):
    st, data = gh_api('GET', f'/repos/{repo}/git/ref/heads/{branch}', token)
    if st != 200:
        raise RuntimeError(f'get ref failed: {st} {data.get("message")}')
    return data['object']['sha']

def api_create_branch(repo: str, token: str, base: str, branch: str):
    base_sha = api_get_ref(repo, token, base)
    st, data = gh_api('POST', f'/repos/{repo}/git/refs', token, body={
        'ref': f'refs/heads/{branch}',
        'sha': base_sha
    })
    if st in (200, 201):
        return True
    msg = (data.get('message') or '')
    if 'Reference already exists' in msg:
        return True
    raise RuntimeError(f'create branch failed: {st} {msg}')

def api_put_file(repo: str, token: str, branch: str, path_in_repo: str, content_bytes: bytes, message: str):
    import base64
    b64 = base64.b64encode(content_bytes).decode('utf-8')
    st0, data0 = gh_api('GET', f'/repos/{repo}/contents/{path_in_repo}?ref={branch}', token)
    sha = None
    if st0 == 200 and isinstance(data0, dict):
        sha = data0.get('sha')
    body = {
        'message': message,
        'content': b64,
        'branch': branch
    }
    if sha:
        body['sha'] = sha
    st, data = gh_api('PUT', f'/repos/{repo}/contents/{path_in_repo}', token, body=body)
    if st not in (200, 201):
        raise RuntimeError(f'put file failed: {st} {data.get("message")}')
    return True
def _git_push_with_token(local_path: Path, branch: str, repo: str, token: str, timeout_s: int = 120):
    """Sicherer Git-Push mit Token und Timeout."""
    ensure_git()
    # Original URL sichern
    orig_url = git(["remote", "get-url", "origin"], cwd=local_path, check=True)
    
    # Token in URL einbetten
    from urllib.parse import quote
    safe_tok = quote(token, safe="")
    temp_url = "https://x-access-token:" + safe_tok + "@github.com/" + repo + ".git"
    
    # Remote temporär umstellen
    git(["remote", "set-url", "origin", temp_url], cwd=local_path, check=True)
    
    try:
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GCM_INTERACTIVE"] = "Never"
        
        p = subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=local_path,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env
        )
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    finally:
        # Remote zurücksetzen
        try:
            git(["remote", "set-url", "origin", orig_url], cwd=local_path, check=True)
        except Exception:
            pass

def api_push_changed_files(repo: str, token: str, branch: str, local_path: Path, commit_msg: str, limit_to_route: str = ""):
    """Fallback: Dateien per GitHub Contents API in den Branch schreiben."""
    # Branch sicherstellen
    api_create_branch(repo, token, base="main", branch=branch)
    
    # Geänderte Dateien bestimmen
    out = git(["status", "--porcelain"], cwd=local_path, check=True)
    files = []
    for line in out.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        if not path:
            continue
        if limit_to_route:
            norm = path.replace("/", "\\")
            if not norm.lower().startswith(limit_to_route.replace("/", "\\").lower().rstrip("\\") + "\\"):
                continue
        files.append(path)
    
    pushed = []
    for fp in files:
        p = (local_path / fp)
        if p.exists() and p.is_file():
            api_put_file(repo, token, branch, fp.replace("\\", "/"), p.read_bytes(), commit_msg)
            pushed.append(fp)
    
    return pushed

def ensure_git():
    if not shutil.which("git"):
        raise SystemExit("git nicht gefunden. Installiere Git for Windows.")
    return True

def git(args, cwd=None, check=True):
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or "git failed")[:800])
    return p.stdout.strip()

def repo_exists(local_path: Path):
    return (local_path / ".git").exists()

def clone_if_needed(repo: str, local_path: Path):
    ensure_git()
    local_path.parent.mkdir(parents=True, exist_ok=True)
    if not repo_exists(local_path):
        log(f"clone: {repo} -> {local_path}")
        git(["clone", f"https://github.com/{repo}.git", str(local_path)], check=True)

def checkout_update(local_path: Path, base: str):
    ensure_git()
    git(["fetch", "origin", "--prune"], cwd=local_path, check=True)
    git(["checkout", base], cwd=local_path, check=True)
    git(["pull", "--ff-only", "origin", base], cwd=local_path, check=True)

def create_branch(local_path: Path, base: str, branch: str):
    ensure_git()
    
    # First, try to delete the branch if it exists locally (to start fresh)
    try:
        git(["branch", "-D", branch], cwd=local_path, check=False)
    except:
        pass
    
    # Try to delete the branch from origin if it exists
    try:
        git(["push", "origin", "--delete", branch], cwd=local_path, check=False)
    except:
        pass
    
    # Now create fresh branch from origin/base and switch to it
    try:
        result = git(["checkout", "-B", branch, f"origin/{base}"], cwd=local_path, check=True)
        print(f"Created branch: {branch} from origin/{base}")
        return
    except Exception as e:
        print(f"Method 1 failed: {e}")
    
    # If that fails, try from local base
    try:
        checkout_update(local_path, base)
        result = git(["checkout", "-B", branch], cwd=local_path, check=True)
        print(f"Created branch: {branch} from local")
        return
    except Exception as e:
        print(f"Method 2 failed: {e}")
    
    # Last resort: just switch to branch if it exists
    try:
        result = git(["checkout", branch], cwd=local_path, check=True)
        print(f"Switched to existing branch: {branch}")
    except Exception as e:
        print(f"ALL METHODS FAILED: {e}")
        raise RuntimeError(f"Could not create or switch to branch {branch}")

def seed_route(local_path: Path, route: str, task: str):
    """Create a small seed project in route so Codex has concrete files to edit."""
    target = local_path / route
    target.mkdir(parents=True, exist_ok=True)
    
    calc = target / "calculator.py"
    if not calc.exists():
        calc.write_text(
            "# Simple calculator (seed)\n"
            "def add(a,b): return a+b\n"
            "def sub(a,b): return a-b\n"
            "def mul(a,b): return a*b\n"
            "def div(a,b):\n"
            "    if b==0: raise ZeroDivisionError('division by zero')\n"
            "    return a/b\n\n"
            "def main():\n"
            "    print('Calculator seed. Improve me!')\n\n"
            "if __name__ == '__main__':\n"
            "    main()\n",
            encoding="utf-8",
        )
        log(f"Created seed: {calc}")
    
    readme = target / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# Codex Task Seed\n\nTask:\n\n{task}\n\n"
            "## Goal\n- Nice CLI calculator\n- Add tests\n- Improve error handling\n",
            encoding="utf-8",
        )
        log(f"Created seed: {readme}")

def commit_push(local_path: Path, branch: str, msg: str, repo: str = None, token: str = None, route_limit: str = ""):
    """Commit lokal + Push. Wenn Push hängt/fehlschlägt -> API-Fallback."""
    ensure_git()
    git(["add", "-A"], cwd=local_path, check=True)
    status = git(["status", "--porcelain"], cwd=local_path, check=True)
    
    if not status.strip():
        log("Nothing to commit")
        return
    
    git(["commit", "-m", msg], cwd=local_path, check=True)
    
    # Kein remote push nötig wenn repo/token fehlen
    if not repo or not token:
        log("repo or token missing - skipping push")
        return
    
    # 1) Versuche sicheren Push mit Token/Timeout
    try:
        rc, so, se = _git_push_with_token(local_path, branch, repo, token, timeout_s=120)
        if rc == 0:
            log(f"Pushed via git: {branch}")
            return
        else:
            log(f"git push failed rc={rc}: {se[-300:]}")
    except subprocess.TimeoutExpired:
        log("git push TIMEOUT -> fallback to API")
    except Exception as e:
        log(f"git push exception -> fallback to API: {str(e)[:200]}")
    
    # 2) Fallback: API upload changed files
    log("Using API fallback to push files...")
    pushed_files = api_push_changed_files(repo, token, branch, local_path, commit_msg=msg, limit_to_route=route_limit)
    log(f"Pushed via API: {len(pushed_files)} files")
    try:
        # Use non-interactive git push with timeout
        result = subprocess.run(
            ["git", "push", "-u", "origin", branch],
            cwd=local_path,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        if result.returncode == 0:
            log(f"Pushed via git: {branch}")
            return
        else:
            log(f"Git push failed: {result.stderr[:100]}")
    except subprocess.TimeoutExpired:
        log("Git push timed out - will use API fallback")
    except Exception as e:
        log(f"Git push error: {e}")
    
    # === FALLBACK: Use GitHub API ===
    log("Using API fallback to push files...")
    
    # Get repo name from remote
    remote_url = git(["remote", "get-url", "origin"], cwd=local_path, check=True)
    # Extract owner/repo from URL like https://github.com/owner/repo.git
    repo = remote_url.replace("https://github.com/", "").replace(".git", "")
    
    # Get token
    token = load_token()
    if not token:
        raise RuntimeError("No token available for API fallback")
    
    # Upload each file
    import os
    for root, dirs, files in os.walk(local_path):
        # Skip .git directory
        if '.git' in root:
            continue
        
        for file in files:
            filepath = Path(root) / file
            rel_path = filepath.relative_to(local_path).as_posix()
            
            # Skip certain files
            if file.startswith('.') or file.endswith('.pyc'):
                continue
            
            try:
                content = filepath.read_bytes()
                api_put_file(repo, token, branch, rel_path, content, msg)
                log(f"Uploaded via API: {rel_path}")
            except Exception as e:
                log(f"Skipped {rel_path}: {e}")
    
    log(f"Committed and pushed via API: {msg[:50]}")

def create_issue(repo: str, token: str, branch: str, task: str):
    title = f"[Codex] {task[:80]}"
    body = (
        "## Codex Aufgabe\n\n"
        f"Task: {task}\n\n"
        f"Branch: {branch}\n\n"
        "Anweisungen:\n"
        f"- Arbeite im Branch {branch}\n"
        "- Erstelle einen Pull Request nach main (base) wenn fertig\n"
        "- Achte auf sauberen, funktionierenden Code\n\n"
        f"@codex Bitte erledige diese Aufgabe im Branch {branch} und stelle einen PR nach main.\n"
    )
    st, data = gh_api(
        "POST", f"/repos/{repo}/issues", token, body={"title": title, "body": body, "labels": ["codex", "automation"]},
    )
    if st not in (200, 201):
        raise RuntimeError(f"issue create failed: {st} {data.get('message')}")
    return data.get("html_url", ""), data.get("number", None)

def create_pr(repo: str, token: str, head: str, base: str, title: str, body: str, draft: bool = False):
    st, data = gh_api(
        "POST",
        f"/repos/{repo}/pulls",
        token,
        body={
            "title": title,
            "head": head,
            "base": base,
            "body": body,
            "draft": draft,
        },
    )
    if st not in (200, 201):
        raise RuntimeError(f"PR create failed: {st} {data.get('message')}")
    return data.get("html_url", ""), data.get("number", None)

def comment_pr(repo: str, token: str, pr_number: int, comment: str):
    # PR comments laufen über issues/{number}/comments
    st, data = gh_api(
        "POST",
        f"/repos/{repo}/issues/{pr_number}/comments",
        token,
        body={"body": comment},
    )
    if st not in (200, 201):
        raise RuntimeError(f"comment failed: {st} {data.get('message')}")
    return True

# Alias for compatibility
comment_issue = comment_pr

def list_open_prs(repo: str, token: str, base: str):
    st, prs = gh_api("GET", f"/repos/{repo}/pulls?state=open&base={base}&per_page=100", token)
    if st != 200:
        raise RuntimeError(f"list PRs failed: {st} {prs.get('message')}")
    return prs

def is_codex_pr(pr):
    labels = {l.get("name") for l in (pr.get("labels") or [])}
    head = (pr.get("head") or {}).get("ref") or ""
    title = pr.get("title") or ""
    return ("codex" in labels) or head.startswith("codex-") or ("[Codex]" in title)

def merge_pr(repo: str, token: str, pr_number: int, method="squash"):
    st, data = gh_api("PUT", f"/repos/{repo}/pulls/{pr_number}/merge", token, body={"merge_method": method})
    ok = st in (200, 201)
    return ok, st, data.get("message", "")

def github_request(method, endpoint, data=None, token=None):
    if not token:
        token = load_token()
    if not token:
        return {"error": "No GitHub token"}
    
    import urllib.request
    import urllib.parse
    
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, headers=headers, method=method)
    if data:
        req.data = json.dumps(data).encode("utf-8")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {"status": resp.status, "data": json.loads(resp.read().decode("utf-8"))}
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "details": e.read().decode("utf-8")[:500]}
    except Exception as e:
        return {"error": str(e)}

def get_default_branch(repo):
    result = github_request("GET", f"/repos/{repo}")
    if "error" in result:
        return "main"
    return result.get("data", {}).get("default_branch", "main")

def create_branch(repo, branch_name, base_branch=None):
    if not base_branch:
        base_branch = get_default_branch(repo)
    
    # Get SHA of base branch
    ref_result = github_request("GET", f"/repos/{repo}/git/ref/heads/{base_branch}")
    if "error" in ref_result:
        return ref_result
    
    sha = ref_result.get("data", {}).get("object", {}).get("sha")
    if not sha:
        return {"error": "SHA not found"}
    
    # Create new branch
    result = github_request("POST", f"/repos/{repo}/git/refs", {
        "ref": f"refs/heads/{branch_name}",
        "sha": sha
    })
    
    # Handle "already exists" error
    if "error" in result and "already exists" in result.get("details", "").lower():
        return {"status": 200, "data": {"ref": f"refs/heads/{branch_name}", "object": {"sha": sha}}}
    return result

def push_file(repo, branch, filepath, content, message):
    import base64
    
    # Check if file exists
    existing = github_request("GET", f"/repos/{repo}/contents/{filepath}?ref={branch}")
    sha = None
    if existing.get("status") == 200:
        sha = existing.get("data", {}).get("sha")
    
    encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    data = {
        "message": message,
        "content": encoded,
        "branch": branch
    }
    if sha:
        data["sha"] = sha
    
    return github_request("PUT", f"/repos/{repo}/contents/{filepath}", data)

def create_issue(repo, title, body, labels=None):
    data = {
        "title": title,
        "body": body
    }
    if labels:
        data["labels"] = labels
    
    return github_request("POST", f"/repos/{repo}/issues", data)

def get_open_prs(repo, base_branch="main"):
    result = github_request("GET", f"/repos/{repo}/pulls?state=open&base={base_branch}&sort=created&direction=desc")
    if "error" in result:
        return []
    return result.get("data", [])

def merge_pr(repo, pr_number):
    return github_request("PUT", f"/repos/{repo}/pulls/{pr_number}/merge", {
        "merge_method": "merge"
    })

def git_pull(repo_path):
    repo_path = Path(repo_path)
    if not repo_path.exists():
        log(f"Repo not found: {repo_path}")
        return False
    
    try:
        # Check if it's a git repo
        if not (repo_path / ".git").exists():
            log(f"Not a git repo: {repo_path}")
            # Clone it
            remote_url = "https://github.com/SellTekk/Jarvis-Scripts.git"
            subprocess.run(["git", "clone", remote_url, str(repo_path)], check=True, capture_output=True)
            log(f"Cloned repo to {repo_path}")
        
        # Pull from main
        result = subprocess.run(["git", "pull", "origin", "main"], cwd=repo_path, capture_output=True, text=True)
        log(f"Git pull: {result.stdout}")
        return True
    except Exception as e:
        log(f"Git error: {e}")
        return False

def dispatch(args):
    repo = args.repo
    task = args.task
    local = args.local
    base = args.base or "main"
    route = args.route or "codex_tasks/calculator"
    
    token = load_token()
    if not token:
        raise SystemExit("Token fehlt. Setze GITHUB_TOKEN oder GH_TOKEN.")
    
    print(f"=== DISPATCH: {task} ===")
    print(f"Repo: {repo}, Base: {base}, Route: {route}")
    
    # Handle local repo path
    if not local:
        local = str(Path.home() / ".openclaw" / "repos" / repo.split("/")[-1])
    
    local_path = Path(local)
    
    # Clone if needed
    print("Cloning if needed...")
    clone_if_needed(repo, local_path)
    
    # Update to base branch first
    print(f"Updating to base branch: {base}")
    checkout_update(local_path, base)
    
    # Create branch name
    branch = f"codex-{int(time.time())}"
    print(f"Creating and switching to branch: {branch}")
    
    # Create and switch to new branch - DO THIS DIRECTLY HERE
    ensure_git()
    # First try to delete local branch if exists
    git(["branch", "-D", branch], cwd=local_path, check=False)
    # Now create new branch from origin/base
    result = git(["checkout", "-B", branch, f"origin/{base}"], cwd=local_path, check=True)
    print(f"Branch created and switched to: {branch}")
    
    # Check current branch
    current_branch = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=local_path, check=False)
    print(f"Current branch: {current_branch}")
    
    if current_branch != branch:
        print(f"ERROR: Expected to be on {branch} but on {current_branch}")
    
    # Seed the route with actual files (CRITICAL for Codex!)
    if route:
        print(f"Creating seed files in: {route}")
        seed_route(local_path, route, task)
    
    # Commit and push (this is the key step!)
    print(f"Committing and pushing: {branch}")
    commit_push(
        local_path=local_path,
        branch=branch,
        msg=f"[codex] seed: {task[:60]}",
        repo=repo,
        token=token,
        route_limit=route.replace("/", "\\") if route else ""
    )
    
    # 1) PR erstellen (damit @codex wirklich greift – PR Kontext ist nötig)
    pr_title = f"[Codex] {task[:80]}"
    pr_body = (
        "## Codex Aufgabe\n\n"
        f"Task: {task}\n\n"
        f"Branch: {branch} → Base: {base}\n\n"
        "### Bitte erledigen:\n"
        "- Implementiere die Aufgabe direkt in diesem PR (Commits pushen)\n"
        "- Tests/CI sollen grün sein\n"
    )
    pr_url, pr_no = create_pr(repo, token, head=branch, base=base, title=pr_title, body=pr_body, draft=False)
    log(f"created PR #{pr_no}: {pr_url}")
    
    # 2) Codex Cloud Task triggern: @codex <task> (NICHT Issue, sondern PR-Kommentar!)
    # Laut Doku startet @codex (anything other than 'review') einen Cloud Task im PR-Kontext.
    comment_issue(repo, token, pr_no, f"@codex {task}\n\nBitte committe deine Änderungen in diesen PR und halte CI grün.")
    
    # optional: Issue nur zur Nachverfolgung (nicht als Trigger!)
    issue_url, issue_no = create_issue(repo, token, branch, task)
    
    out = {
        "status":"sent",
        "repo":repo,
        "base":base,
        "branch":branch,
        "pr": pr_url,
        "pr_no": pr_no,
        "issue": issue_url,
        "issue_no": issue_no
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))

def sync(args):
    repo = args.repo
    local = args.local
    base = args.base or "main"
    merge = args.merge
    pull = args.pull
    
    log(f"=== SYNC: {repo} (base={base}) ===")
    
    # Find open PRs from Codex branches
    prs = get_open_prs(repo, base)
    log(f"Found {len(prs)} open PRs")
    
    merged_count = 0
    for pr in prs:
        pr_branch = pr.get("head", {}).get("ref", "")
        if pr_branch.startswith("codex-"):
            pr_number = pr.get("number")
            log(f"Found Codex PR #{pr_number}: {pr_branch}")
            
            if merge:
                log(f"Merging PR #{pr_number}...")
                merge_result = merge_pr(repo, pr_number)
                if "error" in merge_result:
                    log(f"Merge failed: {merge_result}")
                else:
                    log(f"Merged PR #{pr_number}")
                    merged_count += 1
    
    # Pull from main if requested
    if pull and local:
        log(f"Pulling from main to {local}...")
        git_pull(local)
    
    log(f"=== SYNC DONE: {merged_count} PRs merged ===")

def main():
    parser = argparse.ArgumentParser(description="Codex Bridge (Main Routed)")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Dispatch command
    dispatch_parser = subparsers.add_parser("dispatch", help="Dispatch task to Codex")
    dispatch_parser.add_argument("--repo", required=True, help="GitHub repo (owner/repo)")
    dispatch_parser.add_argument("--task", required=True, help="Task description")
    dispatch_parser.add_argument("--local", help="Local folder to upload")
    dispatch_parser.add_argument("--base", default="main", help="Base branch")
    dispatch_parser.add_argument("--route", help="Route/path for the task")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync Codex PRs")
    sync_parser.add_argument("--repo", required=True, help="GitHub repo (owner/repo)")
    sync_parser.add_argument("--local", help="Local repo to pull to")
    sync_parser.add_argument("--base", default="main", help="Base branch")
    sync_parser.add_argument("--merge", action="store_true", help="Merge PRs")
    sync_parser.add_argument("--pull", action="store_true", help="Pull from main")
    
    args = parser.parse_args()
    
    if args.command == "dispatch":
        dispatch(args)
    elif args.command == "sync":
        sync(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()