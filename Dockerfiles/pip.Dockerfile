ARG PY_VERSION=3.7
ARG PIP_TAG

FROM python:${PY_VERSION}-slim

RUN apt-get update && apt-get install --no-install-recommends -y gcc libc6-dev

COPY . /jina/

RUN cd /jina && pip install ."$PIP_TAG"
RUN cat $HOME/.bashrc
RUN grep -Fxq "# JINA_CLI_BEGIN" $HOME/.bashrc

ENTRYPOINT ["jina"]