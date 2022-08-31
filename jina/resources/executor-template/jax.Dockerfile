ARG CUDA_VERSION=11.6.0
ARG CUDNN_VERSION=8

FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu20.04

# declare the image name
ARG JAXLIB_VERSION=0.3.0

# install python3-pip
RUN apt update && apt install python3-pip -y

# install dependencies via pip
RUN python3 -m pip install numpy scipy six wheel jaxlib==${JAXLIB_VERSION}+cuda11.cudnn82 -f https://storage.googleapis.com/jax-releases/jax_releases.html jax[cuda11_cudnn82] -f https://storage.googleapis.com/jax-releases/jax_releases.html

RUN apt-get update && apt-get install --no-install-recommends -y gcc libc6-dev git

ARG JINA_VERSION=

RUN python3 -m pip install --no-cache-dir jina${JINA_VERSION:+==${JINA_VERSION}}

COPY requirements.txt requirements.txt
RUN pip install --default-timeout=1000 --compile -r requirements.txt

COPY . /workdir/
WORKDIR /workdir

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]