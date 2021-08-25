# TODO use fixed jina version for deterministic execution
FROM jinaai/jina

COPY . /workspace
WORKDIR /workspace

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]
