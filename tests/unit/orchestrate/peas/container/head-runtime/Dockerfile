FROM jinaai/jina:test-pip

ADD runtime.py ./
ENV JINA_LOG_LEVEL=DEBUG

ENTRYPOINT ["python", "runtime.py"]