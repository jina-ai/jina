FROM jinaai/jina:test-pip

ADD *.py mwu_encoder.yml ./

ENTRYPOINT ["jina", "pod", "--yaml-path", "mwu_encoder.yml"]