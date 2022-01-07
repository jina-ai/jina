import os
import asyncio
import multiprocessing
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
from jina.types.request.control import ControlRequest


@pytest.fixture
def private_key_cert_chain():
    cur_dir = os.path.dirname(os.path.abspath(__file__))

    with open(f'{cur_dir}/test-ssl.key', 'rb') as f:
        private_key = f.read()

    with open(f'{cur_dir}/test-ssl.pem', 'rb') as f:
        certificate_chain = f.read()

    return (private_key, certificate_chain)


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
    pool._send_requests = lambda messages, connection, endpoint: mock_send(send_mock)

    pool.add_connection(pod='encoder', head=False, address='1.1.1.1:53')
    pool.add_connection(pod='encoder', head=False, address='1.1.1.2:53')
    results = pool.send_request(
        request=ControlRequest(command='STATUS'), pod='encoder', head=False
    )
    assert len(results) == 1
    assert send_mock.call_count == 1
    assert create_mock.call_count == 2

    results = pool.send_request(
        request=ControlRequest(command='STATUS'), pod='encoder', head=False
    )
    assert len(results) == 1
    assert send_mock.call_count == 2
    assert create_mock.call_count == 2

    # indexer was not added yet, so there isnt anything being sent
    results = pool.send_request(
        request=ControlRequest(command='STATUS'), pod='indexer', head=False
    )
    assert len(results) == 0
    assert send_mock.call_count == 2
    assert create_mock.call_count == 2

    # add indexer now so it can be send
    pool.add_connection(pod='indexer', head=False, address='2.1.1.1:53')
    results = pool.send_request(
        request=ControlRequest(command='STATUS'), pod='indexer', head=False
    )
    assert len(results) == 1
    assert send_mock.call_count == 3
    assert create_mock.call_count == 3

    # polling only applies to shards, there are no shards here, so it only sends one message
    pool.add_connection(pod='encoder', head=False, address='1.1.1.3:53')
    results = pool.send_request(
        request=ControlRequest(command='STATUS'),
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
    results = pool.send_request(
        request=ControlRequest(command='STATUS'),
        pod='encoder',
        head=False,
        polling_type=PollingType.ALL,
    )
    assert len(results) == 2
    assert send_mock.call_count == 6
    assert create_mock.call_count == 5

    # sending to one specific shard should only send one message
    results = pool.send_request(
        request=ControlRequest(command='STATUS'),
        pod='encoder',
        head=False,
        polling_type=PollingType.ANY,
        shard_id=1,
    )
    assert len(results) == 1
    assert send_mock.call_count == 7

    # doing the same with polling ALL ignores the shard id
    results = pool.send_request(
        request=ControlRequest(command='STATUS'),
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
    results = pool.send_request(
        request=ControlRequest(command='STATUS'),
        pod='encoder',
        head=False,
        polling_type=PollingType.ANY,
        shard_id=0,
    )
    assert len(results) == 1
    assert send_mock.call_count == 10

    # encoder pod has no head registered yet so sending to the head will not work
    results = pool.send_request(
        request=ControlRequest(command='STATUS'), pod='encoder', head=True
    )
    assert len(results) == 0
    assert send_mock.call_count == 10

    # after registering a head for encoder, sending to head should work
    pool.add_connection(pod='encoder', head=True, address='1.1.1.10:53')
    results = pool.send_request(
        request=ControlRequest(command='STATUS'), pod='encoder', head=True
    )
    assert len(results) == 1
    assert send_mock.call_count == 11

    # after remove the head again, sending will not work
    assert await pool.remove_connection(pod='encoder', head=True, address='1.1.1.10:53')
    assert close_mock_object.call_count == 2
    results = pool.send_request(
        request=ControlRequest(command='STATUS'), pod='encoder', head=True
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
    data_stub_mock = mocker.Mock()
    single_data_stub_mock = mocker.Mock()
    control_stub_mock = mocker.Mock()

    async def close_mock(*args):
        close_mock_object()

    def create_async_channel_mock(*args):
        create_mock()
        channel_mock.close = close_mock
        return single_data_stub_mock, data_stub_mock, control_stub_mock, channel_mock

    monkeypatch.setattr(
        GrpcConnectionPool, 'create_async_channel_stub', create_async_channel_mock
    )
    return close_mock_object, create_mock


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.timeout(5)
async def test_grpc_connection_pool_real_sending():
    server1_ready_event = multiprocessing.Event()
    server2_ready_event = multiprocessing.Event()

    def listen(port, event: multiprocessing.Event):
        class DummyServer:
            async def process_control(self, request, *args):
                returned_msg = ControlRequest(command='DEACTIVATE')
                return returned_msg

        async def start_grpc_server():
            grpc_server = grpc.aio.server(
                options=[
                    ('grpc.max_send_request_length', -1),
                    ('grpc.max_receive_message_length', -1),
                ]
            )

            jina_pb2_grpc.add_JinaControlRequestRPCServicer_to_server(
                DummyServer(), grpc_server
            )
            grpc_server.add_insecure_port(f'localhost:{port}')

            await grpc_server.start()
            event.set()
            await grpc_server.wait_for_termination()

        asyncio.run(start_grpc_server())

    port1 = random_port()
    server_process1 = Process(
        target=listen,
        args=(
            port1,
            server1_ready_event,
        ),
    )
    server_process1.start()

    port2 = random_port()
    server_process2 = Process(
        target=listen,
        args=(
            port2,
            server2_ready_event,
        ),
    )
    server_process2.start()

    time.sleep(0.1)
    server1_ready_event.wait()
    server2_ready_event.wait()

    pool = GrpcConnectionPool()

    pool.add_connection(pod='encoder', head=False, address=f'localhost:{port1}')
    pool.add_connection(pod='encoder', head=False, address=f'localhost:{port2}')
    sent_msg = ControlRequest(command='STATUS')

    results_call_1 = pool.send_request(request=sent_msg, pod='encoder', head=False)
    results_call_2 = pool.send_request(request=sent_msg, pod='encoder', head=False)
    assert len(results_call_1) == 1
    assert len(results_call_2) == 1

    response1, meta = await results_call_1[0]
    assert response1.command == 'DEACTIVATE'

    response2, meta = await results_call_2[0]
    assert response2.command == 'DEACTIVATE'

    await pool.close()
    server_process1.kill()
    server_process2.kill()
    server_process1.join()
    server_process2.join()


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.timeout(5)
async def test_secure_send_request(private_key_cert_chain):
    server1_ready_event = multiprocessing.Event()
    (private_key, certificate_chain) = private_key_cert_chain

    def listen(port, event: multiprocessing.Event):
        class DummyServer:
            async def process_control(self, request, *args):
                returned_msg = ControlRequest(command='DEACTIVATE')
                return returned_msg

        async def start_grpc_server():
            grpc_server = grpc.aio.server(
                options=[
                    ('grpc.max_send_request_length', -1),
                    ('grpc.max_receive_message_length', -1),
                ]
            )

            jina_pb2_grpc.add_JinaControlRequestRPCServicer_to_server(
                DummyServer(), grpc_server
            )
            grpc_server.add_secure_port(
                f'localhost:{port}',
                grpc.ssl_server_credentials((private_key_cert_chain,)),
            )

            await grpc_server.start()
            event.set()
            await grpc_server.wait_for_termination()

        asyncio.run(start_grpc_server())

    port = random_port()
    server_process1 = Process(
        target=listen,
        args=(
            port,
            server1_ready_event,
        ),
    )
    server_process1.start()

    time.sleep(0.1)
    server1_ready_event.wait()
    sent_msg = ControlRequest(command='STATUS')

    result = GrpcConnectionPool.send_request_sync(
        sent_msg, f'localhost:{port}', https=True, root_certificates=certificate_chain
    )

    assert result.command == 'DEACTIVATE'

    result = await GrpcConnectionPool.send_request_async(
        sent_msg, f'localhost:{port}', https=True, root_certificates=certificate_chain
    )

    assert result.command == 'DEACTIVATE'

    server_process1.kill()
    server_process1.join()


def _create_test_data_message():
    return list(
        request_generator(
            '/', DocumentArray([Document(text='input document') for _ in range(10)])
        )
    )[0]
