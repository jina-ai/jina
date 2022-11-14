FROM jinaai/jina:3.11.0-py38-standard

COPY . /jina

WORKDIR /jina

RUN pip install .

ENTRYPOINT ["jina", "executor", "--uses", "/jina/SimpleIndexerTracing/config.yml"]

