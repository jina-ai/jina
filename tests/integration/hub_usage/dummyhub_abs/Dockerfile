FROM jinaai/jina:test-pip

# setup the workspace
COPY . /workspace/

WORKDIR /workspace

ENTRYPOINT ["jina", "excutor", "--uses", "config.yml"]