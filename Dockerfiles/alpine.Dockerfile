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

ENV PYTHONPATH=$PYTHONPATH:/usr/lib/python3.7/dist-packages:/usr/local/lib/python3.7/site-packages:/usr/lib/python3/dist-packages:/usr/local/lib/python3/site-packages

RUN apk add --no-cache py3-pyzmq py3-numpy py3-scipy grpc && \
    ln -s locale.h /usr/include/xlocale.h && \
    pip install . --no-cache-dir --compile && \
    find /usr/lib/python3.7/ -name 'tests' -exec rm -r '{}' + && \
    find /usr/lib/python3.7/site-packages/ -name '*.so' -print -exec sh -c 'file "{}" | grep -q "not stripped" && strip -s "{}"' \; && \
    rm /usr/include/xlocale.h && \
    rm -rf /tmp/* && \
    rm -rf /jina && \
    rm -rf /var/cache/apk/*

WORKDIR /

ENV JINA_VCS_VERSION=$VCS_REF
ENV JINA_BUILD_DATE=$BUILD_DATE

ENTRYPOINT ["jina"]