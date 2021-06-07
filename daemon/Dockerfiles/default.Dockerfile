ARG JINA_VERSION=latest
ARG PY_VERSION=py37

FROM jinaai/jina:$JINA_VERSION-$PY_VERSION-daemon

# ARG COMMANDS

# RUN if [ -n "$COMMANDS" ]; then \
#         echo -e "Excuting `${COMMANDS}`"; \
#         for command in ${COMMANDS}; do \
#             echo "${command}"; \
#             eval "${command}"; \
#         done; \
#     fi

RUN apt-get update && apt-get install --no-install-recommends -y ruby-dev build-essential && \
    gem install fluentd --no-doc

RUN if [ -f requirements.txt ]; then \
        pip install -r requirements.txt; \
    fi

STOPSIGNAL SIGINT
WORKDIR /workspace
