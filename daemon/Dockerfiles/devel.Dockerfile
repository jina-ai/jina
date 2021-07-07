# This is only used during development, hence `jinaai/jina:test-daemon` must always be built before using it.
# docker build --build-arg PIP_TAG=daemon -f Dockerfiles/debianx.Dockerfile -t jinaai/jina:test-daemon .

ARG LOCALTAG=test
FROM jinaai/jina:$LOCALTAG-daemon

ARG PIP_REQUIREMENTS

RUN if [ -n "$PIP_REQUIREMENTS" ]; then \
        echo "Installing ${PIP_REQUIREMENTS}"; \
        for package in ${PIP_REQUIREMENTS}; do \
            pip install "${package}"; \
        done; \
    fi

WORKDIR /workspace
