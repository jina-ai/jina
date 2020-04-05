FROM jinaai/jina:latest

ADD *.py mwu_encoder.yml ./

ENTRYPOINT ["jina", "pod", "--yaml_path", "mwu_encoder.yml"]