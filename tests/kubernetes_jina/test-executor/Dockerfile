# TODO use jina pip test image
# TODO use jina master
FROM jinaai/jina
RUN apt-get -y update && apt-get install -y git
RUN pip install uvicorn
RUN pip install fastapi

RUN pip install bcolors
RUN pip install kubernetes==18.20.0b1
RUN pip install git+https://github.com/jina-ai/jina.git@18e953f5ce53bd99f422111490875ba4a9eb7c39
# setup the workspace
COPY . /workspace
WORKDIR /workspace

RUN export JINA_LOG_LEVEL=debug

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]
