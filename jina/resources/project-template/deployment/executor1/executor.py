from jina import Executor, requests
from docarray import DocList
from docarray.documents import TextDoc


class MyExecutor(Executor):
    @requests
    def foo(self, docs: DocList[TextDoc], **kwargs) -> DocList[TextDoc]:
        docs[0].text = 'hello, world!'
        docs[1].text = 'goodbye, world!'
        return docs
