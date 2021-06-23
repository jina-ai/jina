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
