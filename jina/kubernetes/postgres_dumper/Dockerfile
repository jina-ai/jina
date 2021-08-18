#Postgres
FROM jinahub/d45rawx6:v20-2.0.18
RUN apt-get -y update && apt-get install -y git
RUN pip install uvicorn
RUN pip install fastapi

RUN pip install git+https://github.com/jina-ai/jina.git@feat-kubernetes-mvp

# setup the workspace
COPY deploy.sh /workspace/deploy.sh
WORKDIR /workspace

ENTRYPOINT ["dump.py"]