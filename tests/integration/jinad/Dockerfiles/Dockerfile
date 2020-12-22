FROM jinaai/jinad

RUN apt-get update && apt-get install --no-install-recommends -y gcc libc6-dev

WORKDIR /jina/

ADD setup.py MANIFEST.in requirements.txt extra-requirements.txt README.md ./
ADD cli ./cli/
ADD jina ./jina/

ARG PIP_TAG

RUN pip install ."$PIP_TAG"

# This doesn't start fluentd in the background
# add entrypoint script if fluentd needs to be enabled for tests
ENTRYPOINT ["jinad"]
