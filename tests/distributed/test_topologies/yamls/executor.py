from jina import Executor, requests, DocumentArray


class WorkspaceValidator(Executor):
    @requests
    def foo(self, docs: DocumentArray, *args, **kwargs):
        docs[0].text = self.workspace
