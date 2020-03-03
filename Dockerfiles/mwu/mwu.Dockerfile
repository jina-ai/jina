FROM jinaai/jina:master-debian

ENTRYPOINT ["jina", "pod", "--yaml_path", "route"]