FROM jinaai/jina:test-pip

RUN pip install docarray==0.21.0

WORKDIR /

RUN python -m pip install --no-cache-dir --upgrade pip && \
    cd jina && \
    pip install --ignore-installed -e .[devel] && \
    cd ..

COPY app.py flow.yml /
ENV JINA_LOG_LEVEL=DEBUG
ENTRYPOINT ["python", "app.py"]
