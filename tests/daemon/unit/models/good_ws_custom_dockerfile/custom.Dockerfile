# custom dockerfile has to use jina:*-daemon image to have parital-daemon
FROM jinaai/jina:test-daemon

COPY custom-requirements.txt custom-requirements.txt
RUN pip install --no-cache-dir -r custom-requirements.txt

# run additional custom commands
RUN apt update && apt install -y redis-server
