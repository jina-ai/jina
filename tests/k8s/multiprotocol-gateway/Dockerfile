FROM jinaai/jina:test-pip

COPY . /workdir/
WORKDIR /workdir

ENTRYPOINT ["jina", "gateway", "--uses", "config.yml"]