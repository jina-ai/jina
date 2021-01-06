FROM python:3.7.6-slim

ARG JINAD_PORT=8000

ENV JINAD_PORT ${JINAD_PORT}
ENV JINAVER jina@git+https://github.com/jina-ai/jina.git@master
WORKDIR /jinad/

ADD setup.py README.md requirements.txt Dockerfiles/entrypoint.sh ./
ADD jinad ./jinad
ADD tests/integration/distributed/Dockerfiles/entrypoint.sh ./

RUN chmod +x entrypoint.sh
RUN apt-get update && \
      apt-get install -y git ruby-dev build-essential && \
      gem install fluentd --no-doc

RUN pip install ".[all]" --no-cache-dir

ENTRYPOINT ["bash", "-c", "./entrypoint.sh"]
