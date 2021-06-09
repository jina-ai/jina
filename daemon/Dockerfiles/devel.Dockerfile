ARG LOCALTAG=test

FROM jinaai/jina:$LOCALTAG-daemon

# ARG COMMANDS
ARG PIP_REQUIREMENTS

# RUN if [ -n "$COMMANDS" ]; then \
#         echo -e "Excuting `${COMMANDS}`"; \
#         for command in ${COMMANDS}; do \
#             echo "${command}"; \
#             eval "${command}"; \
#         done; \
#     fi

# RUN apt-get update && apt-get install --no-install-recommends -y ruby-dev build-essential && \
#     gem install fluentd --no-doc

RUN if [ -n "$PIP_REQUIREMENTS" ]; then \
        echo -e "Installing ${PIP_REQUIREMENTS}"; \
        for package in ${PIP_REQUIREMENTS}; do \
            pip install "${package}"; \
        done; \
    fi

WORKDIR /workspace
