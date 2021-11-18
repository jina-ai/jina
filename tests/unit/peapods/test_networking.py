import asyncio
import time
from multiprocessing import Process

import grpc
import pytest

from jina import DocumentArray, Document
from jina.clients.request import request_generator
from jina.enums import PollingType
from jina.helper import random_port
from jina.peapods.networking import ReplicaList, GrpcConnectionPool
from jina.proto import jina_pb2_grpc
from jina.types.message import Message
from jina.types.message.common import ControlMessage


@pytest.mark.asyncio
async def test_connection_list(mocker, monkeypatch):
    _, _ = await _mock_grpc(mocker, monkeypatch)
    connection_list = ReplicaList()
    assert not connection_list.has_connection(address='1.1.1.1')
    connection_list.add_connection(address='1.1.1.1')
    assert connection_list.has_connection(address='1.1.1.1')
    assert not connection_list.has_connection(address='1.1.1.2')

    connection_list.add_connection(address='1.1.1.2')
    assert connection_list.has_connection(address='1.1.1.1')
    assert connection_list.has_connection(address='1.1.1.2')

    assert await connection_list.remove_connection(address='1.1.1.2')
    assert not connection_list.has_connection(address='1.1.1.2')

    connection_list.add_connection(address='1.1.1.2')
    connection_list.add_connection(address='1.1.1.3')

    assert connection_list.get_next_connection()
    assert connection_list.get_next_connection()
    assert connection_list.get_next_connection()
    assert connection_list.get_next_connection()

    assert await connection_list.remove_connection('1.1.1.2')
    assert connection_list.get_next_connection()
    await connection_list.close()


def mock_send(mock):
    mock()
    return None


@pytest.mark.asyncio
async def test_connection_pool(mocker, monkeypatch):
    close_mock_object, create_mock = await _mock_grpc(mocker, monkeypatch)

    pool = GrpcConnectionPool()
    send_mock = mocker.Mock()
    pool._send_messages = lambda messages, connection: mock_send(send_mock)

    pool.add_connection(pod='encoder', head=False, address='1.1.1.1:53')
    pool.add_connection(pod='encoder', head=False, address='1.1.1.2:53')
    results = pool.send_message(
        msg=ControlMessage(command='STATUS'), pod='encoder', head=False
    )
    assert len(results) == 1
    assert send_mock.call_count == 1
    assert create_mock.call_count == 2

    results = pool.send_message(
        msg=ControlMessage(command='STATUS'), pod='encoder', head=False
    )
    assert len(results) == 1
    assert send_mock.call_count == 2
    assert create_mock.call_count == 2

    # indexer was not added yet, so there isnt anything being sent
    results = pool.send_message(
        msg=ControlMessage(command='STATUS'), pod='indexer', head=False
    )
    assert len(results) == 0
    assert send_mock.call_count == 2
    assert create_mock.call_count == 2

    # add indexer now so it can be send
    pool.add_connection(pod='indexer', head=False, address='2.1.1.1:53')
    results = pool.send_message(
        msg=ControlMessage(command='STATUS'), pod='indexer', head=False
    )
    assert len(results) == 1
    assert send_mock.call_count == 3
    assert create_mock.call_count == 3

    # polling only applies to shards, there are no shards here, so it only sends one message
    pool.add_connection(pod='encoder', head=False, address='1.1.1.3:53')
    results = pool.send_message(
        msg=ControlMessage(command='STATUS'),
        pod='encoder',
        head=False,
        polling_type=PollingType.ALL,
    )
    assert len(results) == 1
    assert send_mock.call_count == 4
    assert create_mock.call_count == 4

    # polling only applies to shards, so we add a shard now and expect 2 messages being sent
    pool.add_connection(pod='encoder', head=False, address='1.1.1.3:53', shard_id=1)
    # adding the same connection again is a noop
    pool.add_connection(pod='encoder', head=False, address='1.1.1.3:53', shard_id=1)
    results = pool.send_message(
        msg=ControlMessage(command='STATUS'),
        pod='encoder',
        head=False,
        polling_type=PollingType.ALL,
    )
    assert len(results) == 2
    assert send_mock.call_count == 6
    assert create_mock.call_count == 5

    # sending to one specific shard should only send one message
    results = pool.send_message(
        msg=ControlMessage(command='STATUS'),
        pod='encoder',
        head=False,
        polling_type=PollingType.ANY,
        shard_id=1,
    )
    assert len(results) == 1
    assert send_mock.call_count == 7

    # doing the same with polling ALL ignores the shard id
    results = pool.send_message(
        msg=ControlMessage(command='STATUS'),
        pod='encoder',
        head=False,
        polling_type=PollingType.ALL,
        shard_id=1,
    )
    assert len(results) == 2
    assert send_mock.call_count == 9

    # removing a replica for shard 0 works and does not prevent messages to be sent to the shard
    assert await pool.remove_connection(
        pod='encoder', head=False, address='1.1.1.2:53', shard_id=0
    )
    assert close_mock_object.call_count == 1
    results = pool.send_message(
        msg=ControlMessage(command='STATUS'),
        pod='encoder',
        head=False,
        polling_type=PollingType.ANY,
        shard_id=0,
    )
    assert len(results) == 1
    assert send_mock.call_count == 10

    # encoder pod has no head registered yet so sending to the head will not work
    results = pool.send_message(
        msg=ControlMessage(command='STATUS'), pod='encoder', head=True
    )
    assert len(results) == 0
    assert send_mock.call_count == 10

    # after registering a head for encoder, sending to head should work
    pool.add_connection(pod='encoder', head=True, address='1.1.1.10:53')
    results = pool.send_message(
        msg=ControlMessage(command='STATUS'), pod='encoder', head=True
    )
    assert len(results) == 1
    assert send_mock.call_count == 11

    # after remove the head again, sending will not work
    assert await pool.remove_connection(pod='encoder', head=True, address='1.1.1.10:53')
    assert close_mock_object.call_count == 2
    results = pool.send_message(
        msg=ControlMessage(command='STATUS'), pod='encoder', head=True
    )
    assert len(results) == 0
    assert send_mock.call_count == 11

    # check that remove/add order is handled well
    pool.add_connection(pod='encoder', head=False, address='1.1.1.4:53')
    assert await pool.remove_connection(pod='encoder', head=False, address='1.1.1.1:53')
    assert await pool.remove_connection(pod='encoder', head=False, address='1.1.1.4:53')
    assert close_mock_object.call_count == 4
    assert not (
        await pool.remove_connection(pod='encoder', head=False, address='1.1.1.2:53')
    )

    await pool.close()


async def _mock_grpc(mocker, monkeypatch):
    create_mock = mocker.Mock()
    close_mock_object = mocker.Mock()
    channel_mock = mocker.Mock()
    stub_mock = mocker.Mock()

    async def close_mock(*args):
        close_mock_object()

    def create_async_channel_mock(*args):
        create_mock()
        channel_mock.close = close_mock
        return stub_mock, channel_mock

    monkeypatch.setattr(
        GrpcConnectionPool, 'create_async_channel_stub', create_async_channel_mock
    )
    return close_mock_object, create_mock


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.timeout(5)
async def test_grpc_connection_pool_real_sending():
    def listen(port):
        class DummyServer:
            async def Call(self, msg, *args):
                returned_msg = ControlMessage(command='DEACTIVATE', identity=str(port))
                return returned_msg

        async def start_grpc_server():
            grpc_server = grpc.aio.server(
                options=[
                    ('grpc.max_send_message_length', -1),
                    ('grpc.max_receive_message_length', -1),
                ]
            )

            jina_pb2_grpc.add_JinaDataRequestRPCServicer_to_server(
                DummyServer(), grpc_server
            )
            grpc_server.add_insecure_port(f'localhost:{port}')

            await grpc_server.start()
            await grpc_server.wait_for_termination()

        asyncio.run(start_grpc_server())

    port1 = random_port()
    server_process1 = Process(
        target=listen,
        args=(port1,),
    )
    server_process1.start()

    port2 = random_port()
    server_process2 = Process(
        target=listen,
        args=(port2,),
    )
    server_process2.start()

    time.sleep(0.1)

    pool = GrpcConnectionPool()

    pool.add_connection(pod='encoder', head=False, address=f'localhost:{port1}')
    pool.add_connection(pod='encoder', head=False, address=f'localhost:{port2}')
    sent_msg = ControlMessage(command='STATUS')

    results_call_1 = pool.send_message(msg=sent_msg, pod='encoder', head=False)
    results_call_2 = pool.send_message(msg=sent_msg, pod='encoder', head=False)
    assert len(results_call_1) == 1
    assert len(results_call_2) == 1

    response1 = await results_call_1[0]
    assert response1.request.command == 'DEACTIVATE'

    response2 = await results_call_2[0]
    assert response2.request.command == 'DEACTIVATE'

    await pool.close()
    server_process1.kill()
    server_process2.kill()
    server_process1.join()
    server_process2.join()


def _create_test_data_message():
    req = list(
        request_generator(
            '/', DocumentArray([Document(text='input document') for _ in range(10)])
        )
    )[0]
    msg = Message(None, req, 'test', '123')
    return msg
