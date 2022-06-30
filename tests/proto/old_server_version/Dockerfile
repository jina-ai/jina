ARG JINA_VERSION=latest

FROM jinaai/jina:${JINA_VERSION}

WORKDIR /app

ADD flow.yml flow.yml
ADD exec.py exec.py

ENTRYPOINT ["jina", "flow", "--uses", "flow.yml"]