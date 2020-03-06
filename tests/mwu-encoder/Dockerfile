FROM jinaai/jina:master-debian

ADD *.py mwu_encoder.yml ./

ENTRYPOINT ["jina-entrypoint.sh", "pod", "--yaml_path", "mwu_encoder.yml"]