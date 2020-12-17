FROM jinaai/jina:test-pip

WORKDIR /

RUN apt-get update && \
    apt-get install --no-install-recommends -y git \
                                               curl

RUN python -m pip install --no-cache-dir --upgrade pip && \
    git clone https://github.com/jina-ai/jinad.git && \
    pip install $(grep -ivE "jina" jinad/requirements.txt)

COPY . /

COPY tests/integration/jinad/test_simple_distributed/entrypoint.sh .

RUN chmod +x entrypoint.sh

# make sure that every Pod will have in its local the image
#RUN jina hub build --prune-images --raise-error --host-info --test-uses --daemon tests/intagration/jinad/hub_mwu && \
#    # change the tag to latest to make it independent of jina version.
#    IMAGE_ID=$(docker images --filter=reference='jinahub/pod.encoder.dummy_mwu_encoder' --format "{{.ID}}") && \
#    docker tag $IMAGE_ID jinahub/pod.encoder.dummy_mwu_encoder:latest

ENTRYPOINT ["bash", "-c", "./entrypoint.sh"]
