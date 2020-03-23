FROM python:3.7.6-slim

ARG VCS_REF
ARG BUILD_DATE

LABEL org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.authors="dev-team@jina.ai" \
      org.opencontainers.image.url="https://jina.ai" \
      org.opencontainers.image.documentation="https://docs.jina.ai" \
      org.opencontainers.image.source="https://github.com/jina-ai/jina/commit/$VCS_REF" \
      org.opencontainers.image.version=$JINA_VERSION \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.vendor="Jina AI Limited" \
      org.opencontainers.image.licenses="Apache 2.0" \
      org.opencontainers.image.title="Jina" \
      org.opencontainers.image.description="Jina is the cloud-native neural search solution powered by state-of-the-art AI technology"

RUN apt-get update && apt-get install --no-install-recommends -y \
    python3-numpy python3-scipy python3-zmq python3-protobuf python3-grpcio && \
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=$PYTHONPATH:/usr/lib/python3.7/dist-packages:/usr/local/lib/python3.7/site-packages:/usr/lib/python3/dist-packages:/usr/local/lib/python3/site-packages

WORKDIR /jina/

ADD setup.py MANIFEST.in requirements.txt extra-requirements.txt README.md ./

ADD jina ./jina/


RUN ln -s locale.h /usr/include/xlocale.h && \
    pip install . --no-cache-dir --compile && \
    rm -rf /tmp/* && rm -rf /jina && \
    rm /usr/include/xlocale.h

# run unit test
# this shall be removed once success
#ADD tests /jina/tests/
#RUN jina --version
#WORKDIR /jina/tests
#ENV PYTHONPATH=$PYTHONPATH:/jina/
#ENV JINA_SKIP_CONTAINER_TESTS=TRUE
#RUN python -m unittest *.py -v
#RUN python -c 'f = open("yaml/test-index.yml"); print(f.read())'

WORKDIR /
ENV JINA_VCS_VERSION=$VCS_REF
ENV JINA_BUILD_DATE=$BUILD_DATE

ENTRYPOINT ["jina"]