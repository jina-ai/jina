import logging
from typing import Dict, List, Literal, Optional

import pytest
from docarray import BaseDoc, DocList

from jina import Client, Deployment, Executor, requests
from jina.helper import random_port


class PortGetter:
    def __init__(self):
        self.ports = {
            "http": {
                True: random_port(),
                False: random_port(),
            },
            "grpc": {
                True: random_port(),
                False: random_port(),
            },
        }

    def get_port(self, protocol: Literal["http", "grpc"], include_gateway: bool) -> int:
        return self.ports[protocol][include_gateway]

    @property
    def gateway_ports(self) -> List[int]:
        return [self.ports["http"][True], self.ports["grpc"][True]]

    @property
    def no_gateway_ports(self) -> List[int]:
        return [self.ports["http"][False], self.ports["grpc"][False]]


@pytest.fixture(scope='module')
def port_getter() -> callable:
    getter = PortGetter()
    return getter


class DictDoc(BaseDoc):
    data: dict


class HeaderExecutor(Executor):
    @requests(on="/get-headers")
    def post_endpoint(
        self,
        docs: DocList[DictDoc],
        parameters: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs,
    ) -> DocList[DictDoc]:
        return DocList[DictDoc]([DictDoc(data=headers)])

    @requests(on='/stream-headers')
    async def stream_task(
        self, doc: DictDoc, headers: Optional[dict] = None, **kwargs
    ) -> DictDoc:
        for k, v in sorted((headers or {}).items()):
            yield DictDoc(data={k: v})

        yield DictDoc(data={"DONE": "true"})


@pytest.fixture(scope='module')
def deployment_no_gateway(port_getter: PortGetter) -> Deployment:

    with Deployment(
        uses=HeaderExecutor,
        protocol=["http", "grpc"],
        port=port_getter.no_gateway_ports,
        include_gateway=False,
    ) as dep:
        yield dep


@pytest.fixture(scope='module')
def deployment_gateway(port_getter: PortGetter) -> Deployment:

    with Deployment(
        uses=HeaderExecutor,
        protocol=["http", "grpc"],
        port=port_getter.gateway_ports,
        include_gateway=False,
    ) as dep:
        yield dep


@pytest.fixture(scope='module')
def deployments(deployment_gateway, deployment_no_gateway) -> Dict[bool, Deployment]:
    return {
        True: deployment_gateway,
        False: deployment_no_gateway,
    }


@pytest.mark.parametrize('include_gateway', [False, True])
def test_headers_in_http_headers(include_gateway, port_getter: PortGetter, deployments):
    port = port_getter.get_port("http", include_gateway)
    data = {
        "data": [{"text": "test"}],
        "parameters": {
            "parameter1": "value1",
        },
    }
    logging.info(f"Posting to {port}")
    client = Client(port=port, protocol="http")
    resp = client.post(
        on=f'/get-headers',
        inputs=DocList([DictDoc(data=data)]),
        headers={
            "header1": "value1",
            "header2": "value2",
        },
        return_type=DocList[DictDoc],
    )
    assert resp[0].data['header1'] == 'value1'


@pytest.mark.asyncio
@pytest.mark.parametrize('include_gateway', [False, True])
async def test_headers_in_http_headers_streaming(
    include_gateway, port_getter: PortGetter, deployments
):
    client = Client(
        port=port_getter.get_port("http", include_gateway),
        protocol="http",
        asyncio=True,
    )
    data = {"data": [{"text": "test"}], "parameters": {"parameter1": "value1"}}
    chunks = []

    async for doc in client.stream_doc(
        on=f'/stream-headers',
        inputs=DictDoc(data=data),
        headers={
            "header1": "value1",
            "header2": "value2",
        },
        return_type=DictDoc,
    ):
        chunks.append(doc)
    assert len(chunks) > 2

    assert DictDoc(data={'header1': 'value1'}) in chunks
    assert DictDoc(data={'header2': 'value2'}) in chunks
