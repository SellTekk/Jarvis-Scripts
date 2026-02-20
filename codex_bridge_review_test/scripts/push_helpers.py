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