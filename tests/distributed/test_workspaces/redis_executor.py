import time
import redis
import subprocess

from jina import Executor, requests, DocumentArray, Document


class DummyRedisIndexer(Executor):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.redis_server = subprocess.Popen(
            ['redis-server', '--daemonize', 'yes', '--port', '2374']
        )
        print('sleeping for 2secs to allow redis server to start')
        time.sleep(2)
        self.handler = redis.Redis(host='localhost', port=2374, db=0)
        assert self.handler.ping()

    @requests(on='/index')
    def index(self, docs: DocumentArray, *args, **kwargs):
        self.handler.mset({doc.text: doc.to_base64() for doc in docs})

    @requests(on='/search')
    def search(self, docs: DocumentArray, *args, **kwargs):
        for doc in docs:
            result = self.handler.get(doc.text)
            if result:
                doc.matches = DocumentArray()
                doc.matches.append(Document.from_base64(result))

    def close(self) -> None:
        self.redis_server.kill()
