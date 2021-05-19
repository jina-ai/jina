

def id_cleaner(docker_id: str, prefix: str = 'sha256:') -> str:
    return docker_id[docker_id.startswith(prefix) and len(prefix):][:10]
