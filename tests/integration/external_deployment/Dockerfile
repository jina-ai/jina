FROM jinaai/jina:master

COPY . /executor_root/

WORKDIR /executor_root

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]