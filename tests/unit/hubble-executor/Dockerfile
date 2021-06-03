FROM jinaai/jina:test-pip

ADD *.py *.yml ./

ENTRYPOINT ["jina", "pod", "--uses", "config.yml"]