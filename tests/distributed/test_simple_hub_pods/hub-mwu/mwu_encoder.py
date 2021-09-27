from jina import requests, Executor, DocumentArray


class MWUEncoder(Executor):
    @requests
    def encode(self, docs: DocumentArray, **kwargs) -> DocumentArray:
        for d in docs:
            d.text += ' hurray'
