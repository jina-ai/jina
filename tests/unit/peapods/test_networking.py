import multiprocessing
import time
from multiprocessing import Process
from threading import Event

import pytest

from jina import DocumentArray, Document
from jina.clients.request import request_generator
from jina.parsers import set_pea_parser
from jina.peapods.networking import ConnectionPool, ConnectionList, GrpcConnectionPool
from jina.peapods.runtimes.grpc import GRPCDataRuntime
from jina.types.message import Message
from jina.types.message.common import ControlMessage


def test_connection_list(mocker):
    connection_list = ConnectionList(port=1234)
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
    pool = ConnectionPool()
    pool._create_connection = create_mock
    pool._send_message = send_mock

    pool.send_message(msg=ControlMessage(command='IDLE'), target_address='1.1.1.1:53')
    assert send_mock.call_count == 1
    assert create_mock.call_count == 1

    pool.send_message(msg=ControlMessage(command='IDLE'), target_address='1.1.1.1:53')
    assert send_mock.call_count == 2
    assert create_mock.call_count == 1

    pool.send_message(msg=ControlMessage(command='IDLE'), target_address='1.1.1.2:53')
    print(send_mock.call_count, flush=True)
    assert send_mock.call_count == 3
    assert create_mock.call_count == 2

    pool.close()


def test_connection_pool_same_host(mocker):
    create_mock = mocker.Mock()
    send_mock = mocker.Mock()
    pool = ConnectionPool()
    pool._create_connection = create_mock
    pool._send_message = send_mock

    pool.send_message(msg=ControlMessage(command='IDLE'), target_address='1.1.1.1:53')
    assert send_mock.call_count == 1
    assert create_mock.call_count == 1

    pool.send_message(msg=ControlMessage(command='IDLE'), target_address='1.1.1.1:53')
    assert send_mock.call_count == 2
    assert create_mock.call_count == 1

    pool.send_message(msg=ControlMessage(command='IDLE'), target_address='1.1.1.1:54')
    print(send_mock.call_count, flush=True)
    assert send_mock.call_count == 3
    assert create_mock.call_count == 2

    pool.close()


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.timeout(5)
async def test_grpc_connection_pool():
    args = set_pea_parser().parse_args([])
    is_called = multiprocessing.Event()
    is_cancel = Event()

    def start_runtime(args, is_called, is_cancel):
        with GRPCDataRuntime(args, is_cancel) as runtime:
            runtime._data_request_handler.handle = (
                lambda *args, **kwargs: is_called.set()
            )
            runtime.run_forever()

    runtime_process = Process(
        target=start_runtime,
        args=(args, is_called, is_cancel),
    )
    runtime_process.start()

    assert GRPCDataRuntime.wait_for_ready_or_shutdown(
        timeout=3.0, ctrl_address=f'{args.host}:{args.port_in}', shutdown_event=Event()
    )

    pool = GrpcConnectionPool()
    await pool.send_message(
        msg=_create_test_data_message(), target_address=f'{args.host}:{args.port_in}'
    )

    time.sleep(0.1)

    assert is_called.is_set()
    pool.close()
    GRPCDataRuntime.cancel(cancel_event=is_cancel)
    runtime_process.terminate()
    runtime_process.join()


def _create_test_data_message():
    req = list(
        request_generator(
            '/', DocumentArray([Document(text='input document') for _ in range(10)])
        )
    )[0]
    msg = Message(None, req, 'test', '123')
    return msg
