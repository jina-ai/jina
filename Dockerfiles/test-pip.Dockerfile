ARG PY_VERSION=3.7
ARG PIP_TAG

FROM python:${PY_VERSION}-slim

RUN apt-get update && apt-get install --no-install-recommends -y gcc libc6-dev net-tools procps htop lsof dnsutils

COPY . /jina/

RUN cd /jina && pip install ."$PIP_TAG"
RUN cat $HOME/.bashrc
RUN grep -Fxq "# JINA_CLI_BEGIN" $HOME/.bashrc

ENV JINA_OPTOUT_TELEMETRY='true'
ENV GRPC_ENABLE_FORK_SUPPORT='0'
ENV JINA_LOG_LEVEL='DEBUG'
ENTRYPOINT ["jina"]
