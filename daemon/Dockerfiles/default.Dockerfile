# This is the default dockerfile used for all containers created by JinaD

ARG JINA_VERSION=master
ARG PY_VERSION=py38

FROM jinaai/jina:$JINA_VERSION-$PY_VERSION-daemon

ARG PIP_REQUIREMENTS

RUN if [ -n "$PIP_REQUIREMENTS" ]; then \
    echo "Installing ${PIP_REQUIREMENTS}"; \
    for package in ${PIP_REQUIREMENTS}; do \
    pip install "${package}"; \
    done; \
    fi

STOPSIGNAL SIGINT
