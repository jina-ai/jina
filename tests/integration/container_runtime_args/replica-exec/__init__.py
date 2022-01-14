from jina import Executor, requests


class ReplicatedExec(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docker_id = self.get_docker_id()
        self.shard_id = self.runtime_args.shard_id
        self.shards = self.runtime_args.shards

    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.tags['replica'] = self.docker_id  # identify replicas via docker container id
            doc.tags['shard_id'] = self.shard_id
            doc.tags['shards'] = self.shards

    def get_docker_id(self):
        import subprocess

        bash_command = """head -1 /proc/self/cgroup|cut -d/ -f3"""
        return subprocess.check_output(['bash', '-c', bash_command]).decode("utf-8")
