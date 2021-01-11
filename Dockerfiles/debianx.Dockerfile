# NOTE: The strucutre of this file is optimized for our CICD
# If you try to build Jina locally, please use
# docker build --target jina_base ...
# If you try to build JinaD locally, please use
# docker build ...

# !!! An ARG declared before a FROM is outside of a build stage, so it can’t be used in any instruction after a FROM
ARG PY_VERSION=3.7

FROM python:${PY_VERSION}-slim AS jina_base

ARG VCS_REF
ARG BUILD_DATE
ARG JINA_VERSION
ARG PIP_TAG

LABEL org.opencontainers.image.created=${BUILD_DATE} \
      org.opencontainers.image.authors="dev-team@jina.ai" \
      org.opencontainers.image.url="https://jina.ai" \
      org.opencontainers.image.documentation="https://docs.jina.ai" \
      org.opencontainers.image.source="https://github.com/jina-ai/jina/commit/${VCS_REF}" \
      org.opencontainers.image.version=${JINA_VERSION} \
      org.opencontainers.image.revision=${VCS_REF} \
      org.opencontainers.image.vendor="Jina AI Limited" \
      org.opencontainers.image.licenses="Apache 2.0" \
      org.opencontainers.image.title="Jina" \
      org.opencontainers.image.description="Jina is the cloud-native neural search solution powered by state-of-the-art AI and deep learning technology"

ENV JINA_BUILD_BASE_DEP="python3-grpcio" \
    JINA_BUILD_DEVEL_DEP="build-essential gcc libc-dev python3-gevent libmagic1" \
    PYTHONPATH=$PYTHONPATH:/usr/lib/python${PY_VERSION}/dist-packages:/usr/local/lib/python${PY_VERSION}/site-packages:/usr/lib/python3/dist-packages:/usr/local/lib/python3/site-packages \
    JINA_VERSION=${JINA_VERSION} \
    JINA_VCS_VERSION=${VCS_REF} \
    JINA_BUILD_DATE=${BUILD_DATE} \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY . /jina/

RUN apt-get update && apt-get install --no-install-recommends -y ${JINA_BUILD_BASE_DEP} && \
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/* && \
    ln -s locale.h /usr/include/xlocale.h && \
    cd /jina && \
    pip install . --compile && \
    if [ -n "${PIP_TAG}" ]; then pip install ".[${PIP_TAG}]" --compile; fi && \
    rm -rf /tmp/* && rm -rf /jina && rm /usr/include/xlocale.h

ENTRYPOINT ["jina"]

FROM jina_base AS jina_devel

COPY . /jina/

RUN apt-get update && apt-get install --no-install-recommends -y ruby-dev build-essential && \
    apt-get install --no-install-recommends -y ${JINA_BUILD_DEVEL_DEP} && \
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/* && \
    ln -s locale.h /usr/include/xlocale.h && cd /jina && \
    pip install .[devel] --compile && \
    rm -rf /tmp/* && rm -rf /jina && rm /usr/include/xlocale.h

ENTRYPOINT ["jina"]

FROM jina_base AS jina_daemon

COPY . /jina/

RUN apt-get update && apt-get install --no-install-recommends -y ruby-dev build-essential && \
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/* && \
    gem install fluentd --no-doc && \
    ln -s locale.h /usr/include/xlocale.h && cd /jina && \
    pip install .[daemon] --compile && \
    rm -rf /tmp/* && rm -rf /jina && rm /usr/include/xlocale.h

ENTRYPOINT ["jinad"]