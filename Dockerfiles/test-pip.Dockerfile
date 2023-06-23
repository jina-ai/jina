ARG PY_VERSION=3.7

FROM python:${PY_VERSION}-slim

ARG DOCARRAY_VERSION
ARG PIP_TAG

RUN apt-get update && apt-get install --no-install-recommends -y gcc libc6-dev net-tools procps htop lsof dnsutils pkg-config wget

# Download and extract Go 1.19
RUN wget -q https://golang.org/dl/go1.19.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go1.19.linux-amd64.tar.gz \
    && rm go1.19.linux-amd64.tar.gz

# Set up environment variables for Go
ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/go"
ENV GOBIN="/go/bin"

COPY . /jina/

RUN cd /jina && pip install ."$PIP_TAG"

RUN if [ -z "$DOCARRAY_VERSION" ]; then echo "DOCARRAY_VERSION is not provided"; else pip install docarray==$DOCARRAY_VERSION; fi

RUN cat $HOME/.bashrc
RUN grep -Fxq "# JINA_CLI_BEGIN" $HOME/.bashrc

ENV JINA_OPTOUT_TELEMETRY='true'
ENV GRPC_ENABLE_FORK_SUPPORT='0'
ENV JINA_LOG_LEVEL='DEBUG'
ENTRYPOINT ["jina"]
