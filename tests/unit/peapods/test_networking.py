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


def test_connection_list(mocker):
    connection_list = ReplicaList()
    assert not connection_list.has_connection(address='1.1.1.1')
    first_connection = mocker.Mock()
    connection_list.add_connection(address='1.1.1.1', connection=first_connection)
    assert connection_list.has_connection(address='1.1.1.1')
    assert not connection_list.has_connection(address='1.1.1.2')

    second_connection = mocker.Mock()
    connection_list.add_connection(address='1.1.1.2', connection=second_connection)
    assert connection_list.has_connection(address='1.1.1.1')
    assert connection_list.has_connection(address='1.1.1.2')

    connection_list.remove_connection(address='1.1.1.2')
    assert not connection_list.has_connection(address='1.1.1.2')

    third_connection = mocker.Mock()
    connection_list.add_connection(address='1.1.1.2', connection=second_connection)
    connection_list.add_connection(address='1.1.1.3', connection=third_connection)

    assert connection_list.get_next_connection() == first_connection
    assert connection_list.get_next_connection() == second_connection
    assert connection_list.get_next_connection() == third_connection
    assert connection_list.get_next_connection() == first_connection

    assert connection_list.remove_connection('1.1.1.2') == second_connection
    assert connection_list.get_next_connection() == third_connection


def test_connection_pool(mocker):
    create_mock = mocker.Mock()
    send_mock = mocker.Mock()
    pool = GrpcConnectionPool()
    pool.create_connection = create_mock
    pool._send_message = send_mock

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
    assert pool.remove_connection(
        pod='encoder', head=False, address='1.1.1.2:53', shard_id=0
    )
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
    assert pool.remove_connection(pod='encoder', head=True, address='1.1.1.10:53')
    results = pool.send_message(
        msg=ControlMessage(command='STATUS'), pod='encoder', head=True
    )
    assert len(results) == 0
    assert send_mock.call_count == 11

    # check that remove/add order is handled well
    pool.add_connection(pod='encoder', head=False, address='1.1.1.4:53')
    assert pool.remove_connection(pod='encoder', head=False, address='1.1.1.1:53')
    assert pool.remove_connection(pod='encoder', head=False, address='1.1.1.4:53')
    assert not (pool.remove_connection(pod='encoder', head=False, address='1.1.1.2:53'))

    pool.close()


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
    assert response1.envelope.receiver_id == str(port1)

    response2 = await results_call_2[0]
    assert response2.request.command == 'DEACTIVATE'
    assert response2.envelope.receiver_id == str(port2)

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
