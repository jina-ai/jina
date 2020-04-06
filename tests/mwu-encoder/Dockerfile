FROM jinaai/jina:devel

ADD *.py mwu_encoder.yml ./

ENTRYPOINT ["jina", "pod", "--yaml_path", "mwu_encoder.yml"]