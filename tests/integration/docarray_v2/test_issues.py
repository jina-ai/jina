from typing import List, Optional

from docarray import BaseDoc, DocList

from jina import Executor, Flow, requests


class NestedDoc(BaseDoc):
    value: str


class RootDoc(BaseDoc):
    nested: Optional[NestedDoc]
    num: Optional[int]
    text: str


class NestedSchemaExecutor(Executor):
    @requests(on='/endpoint')
    async def endpoint(self, docs: DocList[RootDoc], **kwargs) -> DocList[RootDoc]:
        rets = DocList[RootDoc]()
        rets.append(RootDoc(text='hello world', nested=NestedDoc(value='test')))
        return rets


def test_issue_6019():
    flow = Flow().add(name='inference', needs='gateway', uses=NestedSchemaExecutor)
    with flow:
        res = flow.post(
            on='/endpoint', inputs=RootDoc(text='hello'), return_type=DocList[RootDoc]
        )
        assert res[0].text == 'hello world'
        assert res[0].nested.value == 'test'
