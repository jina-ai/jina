FROM jinaai/jina:latest-debian

ENV PWD=./

ENTRYPOINT ["jina", "pod", "--yaml_path", "route"]