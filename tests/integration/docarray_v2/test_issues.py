from typing import List, Optional

from docarray import BaseDoc, DocList

from jina import Executor, Flow, requests


class Nested2Doc(BaseDoc):
    value: str


class Nested1Doc(BaseDoc):
    nested: Nested2Doc


class RootDoc(BaseDoc):
    nested: Optional[Nested1Doc]
    num: Optional[int]
    text: str


class OptionalNested1Doc(BaseDoc):
    nested: Optional[Nested2Doc]


class RootDocWithNestedList(BaseDoc):
    nested: Optional[List[OptionalNested1Doc]]
    num: Optional[int]
    text: str


class NestedSchemaExecutor(Executor):
    @requests(on='/endpoint')
    async def endpoint(self, docs: DocList[RootDoc], **kwargs) -> DocList[RootDoc]:
        rets = DocList[RootDoc]()
        rets.append(
            RootDoc(
                text='hello world', nested=Nested1Doc(nested=Nested2Doc(value='test'))
            )
        )
        return rets


class ListNestedSchemaExecutor(Executor):
    @requests(on='/endpoint')
    async def endpoint(
        self, docs: DocList[RootDocWithNestedList], **kwargs
    ) -> DocList[RootDocWithNestedList]:
        rets = DocList[RootDocWithNestedList]()
        rets.append(
            RootDocWithNestedList(
                text='hello world', nested=[Nested1Doc(nested=Nested2Doc(value='test'))]
            )
        )
        return rets


def test_issue_6019():
    flow = Flow().add(name='inference', needs='gateway', uses=NestedSchemaExecutor)
    with flow:
        res = flow.post(
            on='/endpoint', inputs=RootDoc(text='hello'), return_type=DocList[RootDoc]
        )
        assert res[0].text == 'hello world'
        assert res[0].nested.nested.value == 'test'


def test_issue_6019_with_nested_list():
    flow = Flow().add(name='inference', needs='gateway', uses=ListNestedSchemaExecutor)
    with flow:
        res = flow.post(
            on='/endpoint',
            inputs=RootDocWithNestedList(text='hello'),
            return_type=DocList[RootDocWithNestedList],
        )
        assert res[0].text == 'hello world'
        assert res[0].nested[0].nested.value == 'test'
