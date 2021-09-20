FROM jinaai/jina:test-pip

ADD *.py config.yml ./

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]
