# TODO use jina pip test image
# TODO use jina master
FROM jinaai/jina
RUN apt-get -y update && apt-get install -y git
RUN pip install uvicorn
RUN pip install fastapi

RUN pip install bcolors
RUN pip install kubernetes==18.20.0
RUN pip install git+https://github.com/jina-ai/jina.git@feat-kubernetes-mvp
# setup the workspace
COPY . /workspace
WORKDIR /workspace

RUN export JINA_LOG_LEVEL=debug

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]
