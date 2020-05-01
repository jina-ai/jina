FROM python:3.7.6-slim
# python3-scipy
RUN apt-get update && apt-get install --no-install-recommends -y

WORKDIR /jina/

ADD setup.py MANIFEST.in requirements.txt extra-requirements.txt README.md ./

ADD jina ./jina/

ARG PIP_TAG

RUN pip install ."$PIP_TAG"

RUN cat $HOME/.bashrc
RUN grep -Fxq "# Jina CLI Autocomplete" $HOME/.bashrc

ENTRYPOINT ["jina"]