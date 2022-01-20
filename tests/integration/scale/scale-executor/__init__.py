from jina import Executor, requests


class ScalableExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docker_id = self.get_docker_id()
        print(self.docker_id)
        self.shard_id = self.runtime_args.shard_id

    @requests
    def foo(self, docs, **kwargs):
        for doc in docs:
            doc.tags['docker_id'] = self.docker_id
            doc.tags['shard_id'] = self.shard_id

    def get_docker_id(self):
        import subprocess

        bash_command = """head -1 /proc/self/cgroup|cut -d/ -f3"""
        return subprocess.check_output(['bash', '-c', bash_command]).decode("utf-8")
