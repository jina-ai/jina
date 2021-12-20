from jina import DocumentArray, Executor, requests


class MWUEncoder(Executor):
    @requests
    def encode(self, docs: DocumentArray, **kwargs) -> DocumentArray:
        for d in docs:
            d.text += ' hurray'
