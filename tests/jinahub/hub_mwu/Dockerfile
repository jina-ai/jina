FROM jinaai/jina:test-pip

RUN pip install docarray==0.21.0

ADD *.py mwu_encoder.yml ./
ENV JINA_LOG_LEVEL=DEBUG
ENTRYPOINT ["jina", "executor", "--uses", "mwu_encoder.yml"]