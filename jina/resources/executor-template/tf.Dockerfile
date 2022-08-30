ARG TF_PACKAGE_VERSION=latest
FROM tensorflow/tensorflow:${TF_PACKAGE_VERSION}-gpu

RUN apt-get update && apt-get install --no-install-recommends -y gcc libc6-dev git

ARG JINA_VERSION=

RUN python3 -m pip install --no-cache-dir jina${JINA_VERSION:+==${JINA_VERSION}}

COPY gpu_requirements.txt gpu_requirements.txt
RUN pip install --no-cache-dir -r gpu_requirements.txt

COPY . /workdir/
WORKDIR /workdir

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]