FROM jinaai/jina:test-pip

ADD *.py mwu_encoder.yml ./

ENTRYPOINT ["jina", "executor", "--uses", "mwu_encoder.yml"]
