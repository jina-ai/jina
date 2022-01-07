from jina import Document, DocumentArray, Executor, requests
from jina.logging.logger import JinaLogger


class NameChangeExecutor(Executor):
    def __init__(self, runtime_args, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = runtime_args['name']
        self.logger = JinaLogger(self.name)

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        self.logger.info(f'doc count {len(docs)}')
        docs.append(Document(text=self.name))
        return docs
