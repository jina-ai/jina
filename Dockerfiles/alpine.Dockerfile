FROM python:3.7.6-alpine

ARG VCS_REF
ARG BUILD_DATE

LABEL maintainer="dev-team@jina.ai" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/jina-ai/jina/commit/$VCS_REF" \
      org.label-schema.url="https://jina.ai" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="Jina" \
      org.label-schema.description="Jina is the cloud-native semantic search solution powered by SOTA AI technology"

WORKDIR /jina/

ADD setup.py MANIFEST.in requirements.txt extra-requirements.txt README.md ./
ADD jina ./jina/

RUN apk add --no-cache \
            --virtual=.build-dependencies \
            build-base g++ gfortran file binutils zeromq-dev \
            musl-dev python3-dev openblas-dev && \
    apk add --no-cache libstdc++ openblas libzmq && \
    ln -s locale.h /usr/include/xlocale.h && \
    pip install . --no-cache-dir --compile && \
    find /usr/lib/python3.7/ -name 'tests' -exec rm -r '{}' + && \
    find /usr/lib/python3.7/site-packages/ -name '*.so' -print -exec sh -c 'file "{}" | grep -q "not stripped" && strip -s "{}"' \; && \
    rm /usr/include/xlocale.h && \
    rm -rf /tmp/* && \
    rm -rf /jina && \
    apk del .build-dependencies && \
    rm -rf /var/cache/apk/*

WORKDIR /

ENV JINA_VCS_VERSION=$VCS_REF
ENV JINA_BUILD_DATE=$BUILD_DATE

ENTRYPOINT ["jina"]