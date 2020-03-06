FROM python:3.7.6-slim

ARG VCS_REF
ARG BUILD_DATE

LABEL maintainer="dev-team@jina.ai" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/jina-ai/jina/commit/$VCS_REF" \
      org.label-schema.url="https://jina.ai" \
      org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="Jina" \
      org.label-schema.description="Jina is the cloud-native semantic search solution powered by SOTA AI technology"

RUN apt-get update && apt-get install --no-install-recommends -y python3-numpy python3-scipy && \
    apt-get autoremove && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PYTHONPATH=$PYTHONPATH:/usr/lib/python3.7/dist-packages:/usr/local/lib/python3.7/site-packages:/usr/lib/python3/dist-packages:/usr/local/lib/python3/site-packages

WORKDIR /jina/

ADD setup.py MANIFEST.in requirements.txt extra-requirements.txt README.md ./

ADD jina ./jina/

RUN ln -s locale.h /usr/include/xlocale.h && \
    pip install . --no-cache-dir --compile && \
    rm -rf /tmp/* && rm -rf /jina && \
    rm /usr/include/xlocale.h

WORKDIR /

ENV JINA_VCS_VERSION=$VCS_REF
ENV JINA_BUILD_DATE=$BUILD_DATE

ENTRYPOINT ["jina"]