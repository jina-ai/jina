from jina import DocumentArray, Executor, requests


class TestExecutor(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from jina.logging.logger import JinaLogger

        self.logger = JinaLogger(self.__class__.__name__)
        self._name = self.runtime_args.name

    @requests()
    def fail(self, docs: DocumentArray, **kwargs):
        self.logger.debug(
            f'Received doc array in failing-executor {self._name} with length {len(docs)}.'
        )
        raise RuntimeError('expected error')
