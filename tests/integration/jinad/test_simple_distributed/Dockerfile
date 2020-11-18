FROM python:3.7.6-slim
FROM jinaai:jina:test-pip

WORKDIR /

RUN apt-get update && \
    apt-get install --no-install-recommends -y git \
                                               curl

COPY tests/integration/jinad/test_simple_distributed/requirements.txt /requirements.txt

RUN python -m pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r tests/integration/jinad/test_simple_distributed/requirements.txt

RUN git clone https://github.com/jina-ai/jinad.git && \
    pip install --no-cache-dir --ignore-installed -r jinad/requirements.txt

COPY . /

ENTRYPOINT ["python", "jinad/jinad/main.py"]