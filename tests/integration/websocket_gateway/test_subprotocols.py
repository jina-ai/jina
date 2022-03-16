import asyncio
import time
from multiprocessing import Event, Process

import aiohttp
import pytest

from jina import DocumentArray, Executor, Flow, requests
from jina.types.request.data import DataRequest

INPUT_DA_LEN = 2
NUM_CLIENTS = 3
GATEWAY_PORT = 12345


class DummyExecutor(Executor):
    @requests(on='/foo')
    def foo(self, docs: DocumentArray, **kwargs):
        for d in docs:
            d.text += f'{d.id} is fooed!'


def ws_flow(start_event, stop_event):
    with Flow(protocol='websocket', port_expose=GATEWAY_PORT).add(
        uses=DummyExecutor
    ) as f:
        start_event.set()
        f.block(stop_event=stop_event)


def input_da_gen():
    for i in range(5):
        yield DocumentArray.empty(INPUT_DA_LEN)
        time.sleep(1)


def json_requestify(da: DocumentArray, exec_endpoint='/foo'):
    return {
        'execEndpoint': exec_endpoint,
        'data': {'docs': da.to_dict()},
    }


def bytes_requestify(da: DocumentArray, exec_endpoint='/foo'):
    r = DataRequest()
    r._pb_body.header.exec_endpoint = exec_endpoint
    r.data.docs_bytes = da.to_bytes()
    return r.to_bytes()


@pytest.fixture
def flow_context():
    start_event = Event()
    stop_event = Event()
    p = Process(
        target=ws_flow,
        args=(
            start_event,
            stop_event,
        ),
    )
    p.start()
    start_event.wait()
    yield
    stop_event.set()
    p.join()


async def json_sending_client():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(
            f'ws://localhost:{GATEWAY_PORT}/',
        ) as ws:
            for da in input_da_gen():
                request = json_requestify(da)
                await ws.send_json(request)
                response = await ws.receive_json()
                assert isinstance(response, dict)
                assert response['header']['exec_endpoint'] == '/foo'
                assert len(response['data']) == INPUT_DA_LEN
                for doc in response['data']:
                    assert doc['text'] == f'{doc["id"]} is fooed!'


async def bytes_sending_client():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(
            f'ws://localhost:{GATEWAY_PORT}/',
            protocols=('bytes',),
        ) as ws:
            for da in input_da_gen():
                request = bytes_requestify(da)
                await ws.send_bytes(request)
                response = await ws.receive_bytes()
                assert isinstance(response, bytes)
                dict_response = DataRequest(response).to_dict()
                assert dict_response['header']['exec_endpoint'] == '/foo'
                assert len(dict_response['data']) == INPUT_DA_LEN
                for doc in dict_response['data']:
                    assert doc['text'] == f'{doc["id"]} is fooed!'


@pytest.mark.asyncio
async def test_json_single_client(flow_context):
    await json_sending_client()


@pytest.mark.asyncio
async def test_json_multiple_clients(flow_context):
    await asyncio.wait([json_sending_client() for i in range(NUM_CLIENTS)])


@pytest.mark.asyncio
async def test_bytes_single_client(flow_context):
    await bytes_sending_client()


@pytest.mark.asyncio
async def test_bytes_multiple_clients(flow_context):
    await asyncio.wait([bytes_sending_client() for i in range(NUM_CLIENTS)])
