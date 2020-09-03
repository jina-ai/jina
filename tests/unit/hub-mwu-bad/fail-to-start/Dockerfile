FROM jinaai/jina:devel

ADD *.py mwu_encoder.yml ./

ENTRYPOINT ["jina", "pod", "--uses", "mwu_encoder.yml"]