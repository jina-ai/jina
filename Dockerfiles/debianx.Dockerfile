FROM python:3.7.6-slim

ARG VCS_REF
ARG BUILD_DATE
ARG JINA_VERSION

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
      org.opencontainers.image.description="Jina is the cloud-native neural search solution powered by state-of-the-art AI and deep learning technology"

# python3-scipy
RUN apt-get update && apt-get install --no-install-recommends -y \
    python3-numpy python3-zmq python3-protobuf python3-grpcio gcc libc-dev && \
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=$PYTHONPATH:/usr/lib/python3.7/dist-packages:/usr/local/lib/python3.7/site-packages:/usr/lib/python3/dist-packages:/usr/local/lib/python3/site-packages

ENV JINA_VERSION=$JINA_VERSION
ENV JINA_VCS_VERSION=$VCS_REF
ENV JINA_BUILD_DATE=$BUILD_DATE

WORKDIR /jina/

ADD setup.py MANIFEST.in requirements.txt extra-requirements.txt README.md ./

ADD jina ./jina/

RUN ln -s locale.h /usr/include/xlocale.h && \
    if [ "${JINA_VERSION%-devel}" != "${JINA_VERSION}" ]; then pip install .[devel] --no-cache-dir --compile; else pip install . --no-cache-dir --compile; fi && \
    rm -rf /tmp/* && rm -rf /jina && \
    rm /usr/include/xlocale.h

WORKDIR /



ENTRYPOINT ["jina"]