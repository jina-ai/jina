FROM python:3.9-slim

ARG VCS_REF
ARG BUILD_DATE
ARG JINA_VERSION
ARG INSTALL_DEV

LABEL org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.authors="dev-team@jina.ai" \
      org.opencontainers.image.url="https://jina.ai" \
      org.opencontainers.image.documentation="https://docs.jina.ai" \
      org.opencontainers.image.source="https://github.com/jina-ai/jina/commit/$VCS_REF" \
      org.opencontainers.image.version=$JINA_VERSION \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.vendor="Jina AI Limited" \
      org.opencontainers.image.licenses="Apache 2.0" \
      org.opencontainers.image.title="Jina" \
      org.opencontainers.image.description="Jina is the cloud-native neural search solution powered by state-of-the-art AI and deep learning technology"

ENV JINA_BUILD_BASE_DEP="python3-zmq python3-tornado python3-uvloop python3-lz4" \
    JINA_BUILD_DEVEL_DEP="build-essential gcc libc-dev python3-gevent libmagic1"

RUN apt-get update && apt-get install --no-install-recommends -y $JINA_BUILD_BASE_DEP && \
    if [ -n "$INSTALL_DEV" ]; then apt-get install --no-install-recommends -y $JINA_BUILD_DEVEL_DEP; fi && \
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=$PYTHONPATH:/usr/lib/python3.9/dist-packages:/usr/local/lib/python3.9/site-packages:/usr/lib/python3/dist-packages:/usr/local/lib/python3/site-packages \
    JINA_VERSION=$JINA_VERSION \
    JINA_VCS_VERSION=$VCS_REF \
    JINA_BUILD_DATE=$BUILD_DATE \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /jina/

ADD setup.py MANIFEST.in requirements.txt extra-requirements.txt README.md ./
ADD cli ./cli/
ADD jina ./jina/

RUN ln -s locale.h /usr/include/xlocale.h && \
    pip install -U . --compile && pip install google && \
    if [ -n "$INSTALL_DEV" ]; then pip install -U .[devel] --compile; fi && \
    rm -rf /tmp/* && rm -rf /jina && \
    rm /usr/include/xlocale.h

WORKDIR /



ENTRYPOINT ["jina"]