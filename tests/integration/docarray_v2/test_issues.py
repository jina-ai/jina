from typing import List, Optional, Dict

import pytest
from docarray import BaseDoc, DocList
from pydantic import Field

from jina import Executor, Flow, requests, Deployment, Client


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

def test_issue_6084():
    class EnvInfo(BaseDoc):
        history: str = ''

    class A(BaseDoc):
        b: EnvInfo

    class MyIssue6084Exec(Executor):

        @requests
        def foo(self, docs: DocList[A], **kwargs) -> DocList[A]:
            pass

    f = Flow().add(uses=MyIssue6084Exec).add(uses=MyIssue6084Exec)
    with f:
        pass


@pytest.mark.asyncio
async def test_issue_6090():
    class NestedFieldSchema(BaseDoc):
        name: str = "test_name"
        dict_field: Dict = Field(default_factory=dict)

    class MyDocument(BaseDoc):
        text: str = "test"
        nested_field: NestedFieldSchema = Field(default_factory=NestedFieldSchema)
        dict_field: Dict = Field(default_factory=dict)
        bool_field: bool = False

    class MyExecutor(Executor):
        @requests(on="/stream")
        async def stream(
            self, doc: MyDocument, parameters: Optional[Dict] = None, **kwargs
        ) -> MyDocument:
            for i in range(4):
                yield MyDocument(text=f"hello world {doc.text} {i}")

    docs = []
    protocol = "http"
    with Deployment(uses=MyExecutor, protocol=protocol, port=11112) as dep:
        client = Client(port=11112, protocol=protocol, asyncio=True)
        example_doc = MyDocument(text="my input text")
        async for doc in client.stream_doc(
            on="/stream",
            inputs=example_doc,
            input_type=MyDocument,
            return_type=MyDocument,
        ):
            docs.append(doc)

    assert [d.text for d in docs] == [
        "hello world my input text 0",
        "hello world my input text 1",
        "hello world my input text 2",
        "hello world my input text 3",
    ]
    assert docs[0].nested_field.name == "test_name"

