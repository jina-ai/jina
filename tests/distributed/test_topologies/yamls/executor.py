from jina import DocumentArray, Executor, requests


class WorkspaceValidator(Executor):
    @requests
    def foo(self, docs: DocumentArray, *args, **kwargs):
        docs[0].text = self.workspace
