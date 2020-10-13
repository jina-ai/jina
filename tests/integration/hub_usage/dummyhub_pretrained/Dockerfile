FROM jinaai/jina:test-pip

# setup the workspace
COPY . /workspace/

WORKDIR /workspace

# install the third-party requirements
RUN pip install -r requirements.txt


ENTRYPOINT ["jina", "pod", "--uses", "config.yml"]