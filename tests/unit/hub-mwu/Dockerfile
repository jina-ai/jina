FROM jinaai/jina:devel

ADD *.py mwu_encoder.yml ./

ENTRYPOINT ["jina", "pod", "--yaml-path", "mwu_encoder.yml"]