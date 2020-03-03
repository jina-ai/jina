FROM jinaai/jina:master-debian

ADD *.py *.yml ./

ENTRYPOINT ["jina", "pod", "--yaml_path", "mwu_encoder.yml"]