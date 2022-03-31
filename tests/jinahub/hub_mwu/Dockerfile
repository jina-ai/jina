FROM jinaai/jina:test-pip

ADD *.py mwu_encoder.yml ./
ENV JINA_LOG_LEVEL=DEBUG
ENTRYPOINT ["jina", "executor", "--uses", "mwu_encoder.yml"]