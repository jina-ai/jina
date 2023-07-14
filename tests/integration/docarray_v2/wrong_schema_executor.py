from jina import Executor, requests
from docarray import DocList
from docarray.documents import TextDoc


class WrongSchemaExec(Executor):
    @requests
    def foo(self, docs: TextDoc, **kwargs) -> DocList[TextDoc]:
        pass
