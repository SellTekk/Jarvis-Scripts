
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