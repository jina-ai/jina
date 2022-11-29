FROM jinaai/jina:test-pip

COPY . /workdir/
WORKDIR /workdir

pip install streamlit

ENTRYPOINT ["jina", "gateway", "--uses", "config.yml"]