FROM jinaai/jina:test-pip as base

ADD *.py mwu_encoder.yml ./

FROM base

ADD README.md ./

FROM base

ENTRYPOINT ["jina", "pod", "--uses", "mwu_encoder.yml"]