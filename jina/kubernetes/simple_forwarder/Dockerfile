FROM jinaai/jina:2.0.0rc8
RUN apt-get -y update && apt-get install -y git
RUN pip install uvicorn
RUN pip install fastapi
RUN pip install git+https://github.com/jina-ai/jina.git@feat-custom-host-in

# setup the workspace
COPY . /workspace
WORKDIR /workspace

RUN export JINA_LOG_LEVEL=debug

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]