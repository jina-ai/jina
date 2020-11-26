FROM python:3.7.6-slim

RUN apt-get update && apt-get install --no-install-recommends -y gcc libc6-dev

WORKDIR /jina/

ADD setup.py MANIFEST.in requirements.txt extra-requirements.txt README.md ./
ADD cli ./cli/
ADD jina ./jina/

ARG PIP_TAG

RUN pip install ."$PIP_TAG"

RUN cat $HOME/.bashrc
RUN grep -Fxq "# JINA_CLI_BEGIN" $HOME/.bashrc

WORKDIR /

RUN apt-get update && \
      apt-get install -y git ruby-dev build-essential && \
      gem install fluentd --no-doc

ENTRYPOINT ["jina"]