FROM jinaai/jina:test-pip

WORKDIR /

COPY app.py flow.yml /
ENV JINA_LOG_LEVEL=DEBUG
ENTRYPOINT ["python", "app.py"]
