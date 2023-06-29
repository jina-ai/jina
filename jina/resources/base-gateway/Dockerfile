FROM jinaai/jina:latest-py38-standard

COPY . /workdir/
WORKDIR /workdir

ENTRYPOINT ["jina", "gateway", "--uses", "config.yml"]