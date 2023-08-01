import pytest
from jina import Flow, Executor, Deployment, requests, Client
from docarray import BaseDoc, DocList
from jina.helper import random_port
import asyncio


@pytest.mark.parametrize('ctxt_manager', ['deployment', 'flow'])
@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['websocket'], ['grpc', 'http']])
@pytest.mark.parametrize('return_type', ['batch', 'singleton'])
@pytest.mark.parametrize('include_gateway', [True, False])
def test_singleton_return(ctxt_manager, protocols, return_type, include_gateway):
    if 'websocket' in protocols and ctxt_manager != 'flow':
        return
    if not include_gateway and ctxt_manager == 'flow':
        return
    class MySingletonReturnInputDoc(BaseDoc):
        text: str
        price: int

    class MySingletonReturnOutputDoc(BaseDoc):
        text: str
        category: str

    class MySingletonExecutorReturn(Executor):

        @requests(on='/foo')
        def foo(self, docs: DocList[MySingletonReturnInputDoc], **kwargs) -> DocList[MySingletonReturnOutputDoc]:
            return DocList[MySingletonReturnOutputDoc]([MySingletonReturnOutputDoc(text=docs[0].text + '_changed', category=str(docs[0].price + 1))])

        @requests(on='/foo_single')
        def foo_single(self, doc: MySingletonReturnInputDoc, **kwargs) -> MySingletonReturnOutputDoc:
            return MySingletonReturnOutputDoc(text=doc.text + '_changed', category=str(doc.price + 1))

    ports = [random_port() for _ in protocols]

    if ctxt_manager == 'flow':
        ctxt = Flow(ports=ports, protocol=protocols).add(uses=MySingletonExecutorReturn)
    else:
        ctxt = Deployment(ports=ports, protocol=protocols, uses=MySingletonExecutorReturn, include_gateway=include_gateway)

    with ctxt:
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(
                on='/foo', inputs=MySingletonReturnInputDoc(text='hello', price=2), return_type=DocList[MySingletonReturnOutputDoc] if return_type == 'batch' else MySingletonReturnOutputDoc
            )
            if return_type == 'batch':
                assert docs[0].text == 'hello_changed'
                assert docs[0].category == str(3)
            else:
                assert docs.text == 'hello_changed'
                assert docs.category == str(3)

            docs = c.post(
                on='/foo_single', inputs=MySingletonReturnInputDoc(text='hello', price=2), return_type=DocList[MySingletonReturnOutputDoc] if return_type == 'batch' else MySingletonReturnOutputDoc
            )
            if return_type == 'batch':
                assert docs[0].text == 'hello_changed'
                assert docs[0].category == str(3)
            else:
                assert docs.text == 'hello_changed'
                assert docs.category == str(3)


@pytest.mark.parametrize('ctxt_manager', ['deployment', 'flow'])
@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['websocket'], ['grpc', 'http']])
@pytest.mark.parametrize('return_type', ['batch', 'singleton'])
def test_singleton_return_async(ctxt_manager, protocols, return_type):
    if 'websocket' in protocols and ctxt_manager != 'flow':
        return
    class MySingletonReturnInputDoc(BaseDoc):
        text: str
        price: int

    class MySingletonReturnOutputDoc(BaseDoc):
        text: str
        category: str

    class MySingletonExecutorReturn(Executor):

        @requests(on='/foo')
        async def foo(self, docs: DocList[MySingletonReturnInputDoc], **kwargs) -> DocList[MySingletonReturnOutputDoc]:
            await asyncio.sleep(0.01)
            return DocList[MySingletonReturnOutputDoc]([MySingletonReturnOutputDoc(text=docs[0].text + '_changed', category=str(docs[0].price + 1))])

        @requests(on='/foo_single')
        async def foo_single(self, doc: MySingletonReturnInputDoc, **kwargs) -> MySingletonReturnOutputDoc:
            await asyncio.sleep(0.01)
            return MySingletonReturnOutputDoc(text=doc.text + '_changed', category=str(doc.price + 1))

    ports = [random_port() for _ in protocols]

    if ctxt_manager == 'flow':
        ctxt = Flow(ports=ports, protocol=protocols).add(uses=MySingletonExecutorReturn)
    else:
        ctxt = Deployment(ports=ports, protocol=protocols, uses=MySingletonExecutorReturn)

    with ctxt:
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(
                on='/foo', inputs=MySingletonReturnInputDoc(text='hello', price=2), return_type=DocList[MySingletonReturnOutputDoc] if return_type == 'batch' else MySingletonReturnOutputDoc
            )
            if return_type == 'batch':
                assert docs[0].text == 'hello_changed'
                assert docs[0].category == str(3)
            else:
                assert docs.text == 'hello_changed'
                assert docs.category == str(3)

            docs = c.post(
                on='/foo_single', inputs=MySingletonReturnInputDoc(text='hello', price=2), return_type=DocList[MySingletonReturnOutputDoc] if return_type == 'batch' else MySingletonReturnOutputDoc
            )
            if return_type == 'batch':
                assert docs[0].text == 'hello_changed'
                assert docs[0].category == str(3)
            else:
                assert docs.text == 'hello_changed'
                assert docs.category == str(3)

@pytest.mark.parametrize('ctxt_manager', ['deployment', 'flow'])
@pytest.mark.parametrize('protocols', [['grpc'], ['http'], ['websocket'], ['grpc', 'http']])
@pytest.mark.parametrize('return_type', ['batch', 'singleton'])
def test_singleton_in_place(ctxt_manager, protocols, return_type):
    if 'websocket' in protocols and ctxt_manager != 'flow':
        return

    class MySingletonInPlaceDoc(BaseDoc):
        text: str
        price: int


    class MySingletonExecutorInPlace(Executor):

        @requests(on='/foo')
        def foo(self, docs: DocList[MySingletonInPlaceDoc], **kwargs) -> DocList[MySingletonInPlaceDoc]:
            for doc in docs:
                doc.text = doc.text + '_changed'
                doc.price += 1

        @requests(on='/foo_single')
        def foo_single(self, doc: MySingletonInPlaceDoc, **kwargs) -> MySingletonInPlaceDoc:
            doc.text = doc.text + '_changed'
            doc.price += 1

    ports = [random_port() for _ in protocols]

    if ctxt_manager == 'flow':
        ctxt = Flow(ports=ports, protocol=protocols).add(uses=MySingletonExecutorInPlace)
    else:
        ctxt = Deployment(ports=ports, protocol=protocols, uses=MySingletonExecutorInPlace)

    with ctxt:
        for port, protocol in zip(ports, protocols):
            c = Client(port=port, protocol=protocol)
            docs = c.post(
                on='/foo', inputs=MySingletonInPlaceDoc(text='hello', price=2), return_type=DocList[MySingletonInPlaceDoc] if return_type == 'batch' else MySingletonInPlaceDoc
            )
            if return_type == 'batch':
                assert docs[0].text == 'hello_changed'
                assert docs[0].price == 3
            else:
                assert docs.text == 'hello_changed'
                assert docs.price == 3

            docs = c.post(
                on='/foo_single', inputs=MySingletonInPlaceDoc(text='hello', price=2), return_type=DocList[MySingletonInPlaceDoc] if return_type == 'batch' else MySingletonInPlaceDoc
            )
            if return_type == 'batch':
                assert docs[0].text == 'hello_changed'
                assert docs[0].price == 3
            else:
                assert docs.text == 'hello_changed'
                assert docs.price == 3

@pytest.mark.parametrize('protocol', [['grpc'], ['http'], ['http', 'grpc']])
def test_singleton_in_flow_in_the_middle(protocol):
    pass


def test_openapi_json():
    pass

@pytest.mark.parametrize('ctxt_manager', ['flow', 'deployment'])
def test_call_from_requests_as_singleton(ctxt_manager):
    pass



@pytest.mark.parametrize('ctxt_manager', ['flow', 'deployment'])
@pytest.mark.parametrize('protocol', [['grpc'], ['http'], ['http', 'grpc']])
def test_invalid_input_singleton_output_batch(ctxt_manager, protocol):
    pass


@pytest.mark.parametrize('ctxt_manager', ['flow', 'deployment'])
@pytest.mark.parametrize('protocol', [['grpc'], ['http'], ['http', 'grpc']])
def test_invalid_input_batch_output_singleton(ctxt_manager, protocol):
    pass


async def test_async_client():
    pass