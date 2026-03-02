#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bridge_main.py

Codex Bridge (Main Routed)
=========================

Ziel: OpenClaw -> GitHub -> Codex -> GitHub(PR/Branch) -> Merge nach base -> Local Pull.

Praxis-Hinweis:
Codex-Cloud kann in manchen Setups Änderungen erzeugen, aber nicht zuverlässig
in GitHub pushen (z.B. fehlende GitHub-App-Rechte, PR/Fork-Kontext oder
Cloud-Netzwerk/DNS-Probleme). Dieses Script ist deshalb **defensiv** gebaut:

- Labels sind optional (werden, wenn möglich, automatisch angelegt).
- Kommentare/Label-Fehler brechen den Dispatch nicht ab.
- Sync kann "seed-only" PRs überspringen und optional nudgen.

Token: setx GITHUB_TOKEN "ghp_..." (oder GH_TOKEN)
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

STATE_PATH = Path.home() / ".openclaw" / "codex_bridge_state.json"

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

def _state_load() -> dict:
    try:
        if STATE_PATH.exists():
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"tasks": []}

def _state_save(state: dict) -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass

def _state_add_task(repo: str, base: str, branch: str, task: str, pr_no=None, pr_url="", issue_no=None, issue_url=""):
    state = _state_load()
    state.setdefault("tasks", []).insert(0, {
        "ts": int(time.time()),
        "repo": repo,
        "base": base,
        "branch": branch,
        "task": task,
        "pr_no": pr_no,
        "pr_url": pr_url,
        "issue_no": issue_no,
        "issue_url": issue_url,
    })
    state["tasks"] = state["tasks"][:50]
    _state_save(state)

def ensure_label(repo: str, token: str, name: str, color: str = "0e8a16", description: str = "") -> bool:
    """Ensure a label exists; best-effort."""
    if not name:
        return False
    st, _ = gh_api("GET", f"/repos/{repo}/labels/{quote(name)}", token)
    if st == 200:
        return True
    if st not in (404, 410):
        return False
    st2, _ = gh_api("POST", f"/repos/{repo}/labels", token, body={
        "name": name,
        "color": color,
        "description": description or "",
    })
    return st2 in (200, 201)

def safe_add_issue_labels(repo: str, token: str, issue_number: int, labels: list) -> None:
    if not labels:
        return
    for lb in labels:
        try:
            ensure_label(repo, token, lb)
        except Exception:
            pass
    try:
        st, data = gh_api("POST", f"/repos/{repo}/issues/{issue_number}/labels", token, body={"labels": labels})
        if st not in (200, 201):
            log(f"warn: could not add labels to #{issue_number}: {st} {data.get('message')}")
    except Exception as e:
        log(f"warn: label add exception #{issue_number}: {e}")

def safe_comment(repo: str, token: str, issue_number: int, comment: str) -> None:
    try:
        st, data = gh_api("POST", f"/repos/{repo}/issues/{issue_number}/comments", token, body={"body": comment})
        if st not in (200, 201):
            log(f"warn: comment failed #{issue_number}: {st} {data.get('message')}")
    except Exception as e:
        log(f"warn: comment exception #{issue_number}: {e}")

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
    """Secure git push with token and timeout."""
    ensure_git()
    orig_url = git(["remote", "get-url", "origin"], cwd=local_path, check=True)
    from urllib.parse import quote
    safe_tok = quote(token, safe="")
    temp_url = f"https://x-access-token:{safe_tok}@github.com/{repo}.git"
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
        try:
            git(["remote", "set-url", "origin", orig_url], cwd=local_path, check=True)
        except Exception:
            pass

def api_push_changed_files(repo: str, token: str, branch: str, local_path: Path, commit_msg: str, limit_to_route: str = ""):
    # Best-effort; caller usually created branch already.
    try:
        api_create_branch(repo, token, base="main", branch=branch)
    except Exception:
        pass
    out = git(["status", "--porcelain"], cwd=local_path, check=True)
    files = []
    for line in out.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
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
        raise SystemExit("git not found. Install Git for Windows.")
    return True

def git(args, cwd=None, check=True):
    p = subprocess.run(["git"] + args, cwd=cwd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout or "git failed")[:800])
    return p.stdout.strip()

def ensure_git_identity(local_path: Path):
    """Ensure git can create commits (best-effort)."""
    try:
        name = git(["config", "--get", "user.name"], cwd=local_path, check=False).strip()
        email = git(["config", "--get", "user.email"], cwd=local_path, check=False).strip()
        if not name:
            git(["config", "user.name", "openclaw-bot"], cwd=local_path, check=False)
        if not email:
            git(["config", "user.email", "openclaw-bot@users.noreply.github.com"], cwd=local_path, check=False)
    except Exception:
        pass

def repo_exists(local_path: Path):
    return (local_path / ".git").exists()

def clone_if_needed(repo: str, local_path: Path):
    ensure_git()
    if not repo_exists(local_path):
        log(f"cloning {repo} to {local_path}")
        git(["clone", f"https://github.com/{repo}.git", str(local_path)], check=True)

def checkout_update(local_path: Path, base: str):
    ensure_git()
    git(["fetch", "origin", "--prune"], cwd=local_path, check=True)
    git(["checkout", base], cwd=local_path, check=True)
    git(["pull", "--ff-only", "origin", base], cwd=local_path, check=True)

def create_branch(local_path: Path, base: str, branch: str):
    ensure_git()
    try:
        git(["branch", "-D", branch], cwd=local_path, check=False)
    except Exception:
        pass
    try:
        git(["push", "origin", "--delete", branch], cwd=local_path, check=False)
    except Exception:
        pass
    try:
        git(["checkout", "-B", branch, f"origin/{base}"], cwd=local_path, check=True)
        return
    except Exception as e:
        log(f"checkout -B failed: {e}")
    try:
        checkout_update(local_path, base)
        git(["checkout", "-B", branch], cwd=local_path, check=True)
        return
    except Exception as e:
        log(f"fallback branch creation failed: {e}")
    try:
        git(["checkout", branch], cwd=local_path, check=True)
        return
    except Exception as e:
        raise RuntimeError(f"Could not create/switch to branch {branch}: {e}")

def seed_route(local_path: Path, route: str, task: str):
    target = local_path / route
    target.mkdir(parents=True, exist_ok=True)
    calc = target / "calculator.py"
    if not calc.exists():
        calc.write_text(
            "# Simple calculator seed\n"
            "def add(a,b): return a+b\n"
            "def sub(a,b): return a-b\n"
            "def mul(a,b): return a*b\n"
            "def div(a,b):\n"
            "    if b==0: raise ZeroDivisionError('division by zero')\n"
            "    return a/b\n",
            encoding="utf-8",
        )
        log(f"created {calc}")
    readme = target / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# Codex Task Seed\n\nTask:\n\n{task}\n",
            encoding="utf-8",
        )
        log(f"created {readme}")

def add_issue_labels(repo: str, token: str, issue_number: int, labels: list):
    st, data = gh_api("POST", f"/repos/{repo}/issues/{issue_number}/labels", token, body={"labels": labels})
    if st not in (200, 201):
        raise RuntimeError(f"add labels failed: {st} {data.get('message')}")
    return True

def get_issue(repo: str, token: str, number: int):
    st, data = gh_api("GET", f"/repos/{repo}/issues/{number}", token)
    if st != 200:
        raise RuntimeError(f"get issue failed: {st} {data.get('message')}")
    return data

def get_issue_labels(repo: str, token: str, number: int) -> set:
    issue = get_issue(repo, token, number)
    return {l.get("name") for l in (issue.get("labels") or [])}

def comment_issue(repo: str, token: str, issue_number: int, comment: str):
    st, data = gh_api("POST", f"/repos/{repo}/issues/{issue_number}/comments", token, body={"body": comment})
    if st not in (200, 201):
        raise RuntimeError(f"comment failed: {st} {data.get('message')}")
    return True

def create_issue(repo: str, token: str, branch: str, task: str):
    title = f"[Codex] {task[:80]}"
    body = f"@codex\n\nBranch: {branch}\nTask: {task}\n"
    # Labels are best-effort (some repos reject unknown labels).
    st, data = gh_api("POST", f"/repos/{repo}/issues", token, body={"title": title, "body": body})
    if st not in (200, 201):
        raise RuntimeError(f"issue create failed: {st} {data.get('message')}")
    issue_no = data.get("number", None)
    issue_url = data.get("html_url", "")
    if issue_no:
        safe_add_issue_labels(repo, token, issue_no, ["codex", "automation"])
    return issue_url, issue_no

def create_pr(repo: str, token: str, head: str, base: str, title: str, body: str, draft: bool = False, labels: list = None):
    st, data = gh_api("POST", f"/repos/{repo}/pulls", token, body={"title": title, "head": head, "base": base, "body": body, "draft": draft})
    if st not in (200, 201):
        raise RuntimeError(f"PR create failed: {st} {data.get('message')}")
    pr_no = data.get("number")
    pr_url = data.get("html_url", "")
    if labels and pr_no:
        safe_add_issue_labels(repo, token, pr_no, labels)
    return pr_url, pr_no

def list_open_prs(repo: str, token: str, base: str):
    st, prs = gh_api("GET", f"/repos/{repo}/pulls?state=open&base={base}&per_page=100", token)
    if st != 200:
        raise RuntimeError(f"list PRs failed: {st} {prs.get('message')}")
    return prs

def list_issue_comments(repo: str, token: str, issue_number: int):
    st, comments = gh_api("GET", f"/repos/{repo}/issues/{issue_number}/comments?per_page=100", token)
    if st != 200:
        return []
    return comments if isinstance(comments, list) else []

def extract_git_patch_from_text(text: str) -> str:
    """Extract a diff/patch from a comment body (best-effort)."""
    if not text:
        return ""
    t = text.replace("\r\n", "\n")

    # Prefer fenced blocks
    for fence in ("```diff", "```patch", "```\n"):
        idx = t.find(fence)
        while idx != -1:
            start = idx + len(fence)
            end = t.find("```", start)
            if end != -1:
                body = t[start:end].strip("\n")
                if "diff --git" in body:
                    return body.strip() + "\n"
            idx = t.find(fence, idx + 1)

    # Fallback: raw text starting at diff --git
    di = t.find("diff --git")
    if di != -1:
        return t[di:].strip() + "\n"
    return ""

def try_get_patch_from_pr_comments(repo: str, token: str, pr_number: int, prefer_user_contains: str = "codex") -> str:
    comments = list_issue_comments(repo, token, pr_number)
    # scan latest to oldest
    for c in reversed(comments):
        body = (c.get("body") or "")
        user = (c.get("user") or {}).get("login") or ""
        patch = extract_git_patch_from_text(body)
        if not patch:
            continue
        if prefer_user_contains and prefer_user_contains.lower() in user.lower():
            return patch
        # otherwise accept any patch
        return patch
    return ""

def is_codex_pr(pr):
    labels = {l.get("name") for l in (pr.get("labels") or [])}
    head = (pr.get("head") or {}).get("ref") or ""
    title = pr.get("title") or ""
    return ("codex" in labels) or head.startswith("codex-") or ("[Codex]" in title)

def merge_pr(repo: str, token: str, pr_number: int, method="squash"):
    st, data = gh_api("PUT", f"/repos/{repo}/pulls/{pr_number}/merge", token, body={"merge_method": method})
    ok = st in (200, 201)
    return ok, st, data.get("message", "")

def dispatch(args):
    repo = args.repo
    task = args.task
    local = args.local
    base = args.base or "main"
    route = args.route or "codex_tasks/calculator"
    token = load_token()
    if not token:
        raise SystemExit("Token missing. Set GITHUB_TOKEN or GH_TOKEN.")
    if not local:
        local = str(Path.home() / ".openclaw" / "repos" / repo.split('/')[-1])
    local_path = Path(local)
    clone_if_needed(repo, local_path)
    checkout_update(local_path, base)
    branch = f"codex-{int(time.time())}"
    create_branch(local_path, base, branch)
    if route:
        seed_route(local_path, route, task)
    # commit and push
    subprocess.run(["git", "add", "-A"], cwd=local_path, check=True)
    status = subprocess.run(["git", "status", "--porcelain"], cwd=local_path, capture_output=True, text=True)
    if not status.stdout.strip():
        log("nothing to commit")
    else:
        subprocess.run(["git", "commit", "-m", f"[codex] seed: {task[:60]}"] , cwd=local_path, check=True)
        try:
            rc, so, se = _git_push_with_token(local_path, branch, repo, token)
            if rc != 0:
                log(f"git push failed: {se}")
                api_push_changed_files(repo, token, branch, local_path, f"[codex] seed: {task[:60]}")
        except Exception as e:
            log(f"push exception: {e}")
            api_push_changed_files(repo, token, branch, local_path, f"[codex] seed: {task[:60]}")
    # Create issue first (some setups prioritize issue-based triggers)
    issue_url, issue_no = create_issue(repo, token, branch, task)

    body = f"""## Codex Aufgabe

@codex

Task: {task}

Branch: `{branch}`  → Base: `{base}`

### Bitte erledigen
1. Änderungen im Branch `{branch}` machen
2. **Commit + Push** in denselben Branch (damit der PR updatet)
3. Tests/CI sollen grün sein

Hinweis: Falls du (Codex Cloud) nicht pushen kannst, poste bitte ein `diff --git` Patch im PR-Kommentar.
"""

    pr_url, pr_no = create_pr(
        repo,
        token,
        head=branch,
        base=base,
        title=f"[Codex] {task[:80]}",
        body=body,
        labels=["codex", "automation"],
    )

    if pr_no:
        safe_comment(repo, token, pr_no, f"@codex {task}\n\nBitte commit+push deine Änderungen in **diesen** PR-Branch (`{branch}`).")

    if issue_no:
        safe_comment(repo, token, issue_no, f"@codex Task: {task}\n\nBitte arbeite im Branch `{branch}` und update den PR: {pr_url}")

    _state_add_task(repo, base, branch, task, pr_no=pr_no, pr_url=pr_url, issue_no=issue_no, issue_url=issue_url)
    log(f"dispatch done: PR {pr_url}, Issue {issue_url}")

def sync(args):
    repo = args.repo
    local = args.local
    base = args.base or "main"
    merge = args.merge
    pull = args.pull
    token = load_token()
    prs = list_open_prs(repo, token, base)
    merged = 0
    nudged = 0
    patched = 0
    for pr in prs:
        if is_codex_pr(pr):
            pr_no = pr.get("number")

            min_commits = getattr(args, "min_commits", 1) or 1
            commit_count = None
            try:
                stc, commits = gh_api("GET", f"/repos/{repo}/pulls/{pr_no}/commits?per_page=100", token)
                if stc == 200 and isinstance(commits, list):
                    commit_count = len(commits)
            except Exception:
                pass

            # If Codex Cloud cannot push, it may paste a patch in comments.
            # Optionally, we can apply that patch locally and push it into the PR branch.
            if getattr(args, "apply_patches", False) and local and (commit_count is not None and commit_count <= 1):
                try:
                    patch = try_get_patch_from_pr_comments(repo, token, pr_no)
                    if patch:
                        head_ref = ((pr.get("head") or {}).get("ref") or "").strip()
                        if head_ref:
                            local_path = Path(local)
                            ensure_git_identity(local_path)
                            git(["fetch", "origin", head_ref], cwd=local_path, check=False)
                            git(["checkout", "-B", head_ref, f"origin/{head_ref}"], cwd=local_path, check=False)

                            tmp = Path.home() / ".openclaw" / "_codex_patch.diff"
                            tmp.parent.mkdir(parents=True, exist_ok=True)
                            tmp.write_text(patch, encoding="utf-8")

                            ap = subprocess.run(["git", "apply", "--whitespace=fix", str(tmp)], cwd=local_path, capture_output=True, text=True)
                            if ap.returncode == 0:
                                subprocess.run(["git", "add", "-A"], cwd=local_path, check=False)
                                st_out = subprocess.run(["git", "status", "--porcelain"], cwd=local_path, capture_output=True, text=True)
                                if st_out.stdout.strip():
                                    subprocess.run(["git", "commit", "-m", f"[codex] apply patch for PR #{pr_no}"], cwd=local_path, check=False)
                                    rc, so, se = _git_push_with_token(local_path, head_ref, repo, token)
                                    if rc == 0:
                                        patched += 1
                                        # re-check commit count quickly
                                        stc2, commits2 = gh_api("GET", f"/repos/{repo}/pulls/{pr_no}/commits?per_page=100", token)
                                        if stc2 == 200 and isinstance(commits2, list):
                                            commit_count = len(commits2)
                                    else:
                                        log(f"patch push failed PR #{pr_no}: {se}")
                            else:
                                log(f"git apply failed PR #{pr_no}: {(ap.stderr or ap.stdout or '')[:500]}")
                except Exception as e:
                    log(f"patch apply exception PR #{pr_no}: {e}")

            if getattr(args, "nudge", False) and (commit_count is not None and commit_count <= 1):
                safe_comment(repo, token, pr_no, "@codex Reminder: Bitte deine Änderungen commit+push in diesen PR-Branch. Falls push nicht möglich ist, poste bitte ein Patch (diff --git) hier als Kommentar.")
                nudged += 1

            if merge:
                if commit_count is not None and commit_count < min_commits:
                    log(f"skip merge PR #{pr_no}: commit_count={commit_count} < min_commits={min_commits}")
                    continue
                ok, st, msg = merge_pr(repo, token, pr_no)
                if ok:
                    merged += 1
                else:
                    log(f"merge failed PR #{pr_no}: {st} {msg}")
    if pull and local:
        subprocess.run(["git", "pull", "origin", base], cwd=Path(local), check=True)
    log(f"sync done, merged {merged} PRs, patched {patched} PRs, nudged {nudged} PRs")

def status_cmd(args):
    repo = args.repo
    base = args.base or "main"
    token = load_token()
    if not token:
        raise SystemExit("Token missing. Set GITHUB_TOKEN or GH_TOKEN.")
    prs = list_open_prs(repo, token, base)
    codex_prs = [p for p in prs if is_codex_pr(p)]
    log(f"open codex PRs against {base}: {len(codex_prs)}")
    for pr in codex_prs[:25]:
        pr_no = pr.get("number")
        title = pr.get("title")
        updated = pr.get("updated_at")
        stc, commits = gh_api("GET", f"/repos/{repo}/pulls/{pr_no}/commits?per_page=100", token)
        cc = len(commits) if stc == 200 and isinstance(commits, list) else "?"
        log(f"  #{pr_no} commits={cc} updated={updated} title={title}")

    state = _state_load()
    if state.get("tasks"):
        t0 = state["tasks"][0]
        log(f"last dispatch: repo={t0.get('repo')} base={t0.get('base')} branch={t0.get('branch')} pr={t0.get('pr_url')}")

def main():
    parser = argparse.ArgumentParser(description="Codex Bridge (Main Routed)")
    sub = parser.add_subparsers(dest="command")
    d = sub.add_parser("dispatch")
    d.add_argument("--repo", required=True)
    d.add_argument("--task", required=True)
    d.add_argument("--local")
    d.add_argument("--base", default="main")
    d.add_argument("--route")
    s = sub.add_parser("sync")
    s.add_argument("--repo", required=True)
    s.add_argument("--local")
    s.add_argument("--base", default="main")
    s.add_argument("--merge", action="store_true")
    s.add_argument("--pull", action="store_true")
    s.add_argument("--min-commits", type=int, default=1, help="Do not merge PRs with fewer commits than this")
    s.add_argument("--nudge", action="store_true", help="Comment @codex on seed-only PRs")
    s.add_argument("--apply-patches", action="store_true", help="If a PR only has the seed commit, try to apply a diff patch from PR comments and push it")

    st = sub.add_parser("status")
    st.add_argument("--repo", required=True)
    st.add_argument("--base", default="main")
    args = parser.parse_args()
    if args.command == "dispatch":
        dispatch(args)
    elif args.command == "sync":
        sync(args)
    elif args.command == "status":
        status_cmd(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
