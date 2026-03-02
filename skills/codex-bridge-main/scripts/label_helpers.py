def add_issue_labels(repo: str, token: str, issue_number: int, labels: list):
    st, data = gh_api(
        "POST",
        f"/repos/{repo}/issues/{issue_number}/labels",
        token,
        body={"labels": labels},
    )
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