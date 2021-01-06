ARG JINA_VERSION=devel

FROM jinaai/jina:${JINA_VERSION}

WORKDIR /daemon/

ADD daemon ./jinad

RUN apt-get update && \
    apt-get install -y git ruby-dev build-essential && \
    gem install fluentd --no-doc  && \
    chmod +x jinad-entrypoint.sh && \
    pip install . --no-cache-dir

ENTRYPOINT ["bash", "-c", "./entrypoint.sh"]
