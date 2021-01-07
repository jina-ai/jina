FROM jinaai/jinad

RUN apt-get update && apt-get install --no-install-recommends -y gcc libc6-dev

WORKDIR /jina/

ADD setup.py MANIFEST.in requirements.txt extra-requirements.txt README.md ./
ADD cli ./cli/
ADD jina ./jina/
ADD tests/integration/jinad/Dockerfiles/entrypoint.sh ./

ARG PIP_TAG=[test]

RUN chmod +x entrypoint.sh
RUN pip install ."$PIP_TAG"

# This starts both jinad & fluentd in the background
ENTRYPOINT ["bash", "-c", "./entrypoint.sh"]
