FROM jinaai/jina:test-pip

ADD *.py *.yml ./

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]