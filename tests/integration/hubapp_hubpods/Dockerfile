FROM jinaai/jina:test-pip

WORKDIR /

RUN python -m pip install --no-cache-dir --upgrade pip && \
    cd jina && \
    pip install --ignore-installed -e .[devel] && \
    cd ..

COPY tests/integration/hubapp_hubpods/ .

ENTRYPOINT ["python", "app.py"]
