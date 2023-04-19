FROM jinaai/jina:test-pip

ADD executor.py executor.yml ./

ENTRYPOINT ["jina", "executor", "--uses", "executor.yml"]
