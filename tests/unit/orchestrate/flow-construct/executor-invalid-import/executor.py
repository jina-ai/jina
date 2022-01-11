from jina import Executor, DocumentArray, requests

import some.missing.depdency


class InvalidImportExec(Executor):
    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.text = 'done'
