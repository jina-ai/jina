#Postgres
FROM jinahub/d45rawx6:v20-2.0.19
RUN apt-get -y update && apt-get install -y git
RUN pip install uvicorn
RUN pip install fastapi

RUN pip install git+https://github.com/jina-ai/jina.git@feat-kubernetes-mvp

# setup the workspace
COPY dump.py /dump.py
WORKDIR /

ENTRYPOINT ["python", "dump.py"]