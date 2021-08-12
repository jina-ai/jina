import time
from threading import Event, Thread

import pytest

from jina import DocumentArray
from jina.clients.request import request_generator
from jina.parsers import set_pea_parser
from jina.peapods.grpc import Grpclet
from jina.peapods.runtimes.grpc import GRPCDataRuntime
from jina.types.document import Document
from jina.types.message import Message


@pytest.mark.slow
@pytest.mark.timeout(5)
def test_grpc_data_runtime(mocker):
    args = set_pea_parser().parse_args([])
    handle_mock = mocker.Mock()

    def start_runtime(args, handle_mock):
        with GRPCDataRuntime(args) as runtime:
            runtime._data_request_handler.handle = handle_mock
            runtime.run_forever()

    runtime_thread = Thread(
        target=start_runtime,
        args=(
            args,
            handle_mock,
        ),
    )
    runtime_thread.start()

    assert GRPCDataRuntime.wait_for_ready_or_shutdown(
        timeout=5.0, ctrl_address=f'{args.host}:{args.port_in}', shutdown_event=Event()
    )

    Grpclet._create_grpc_stub(f'{args.host}:{args.port_in}', is_async=False).Call(
        _create_test_data_message()
    )
    time.sleep(0.1)
    handle_mock.assert_called()

    GRPCDataRuntime.cancel(f'{args.host}:{args.port_in}')
    runtime_thread.join()

    assert not GRPCDataRuntime.is_ready(f'{args.host}:{args.port_in}')


def _create_test_data_message():
    req = list(
        request_generator(
            '/', DocumentArray([Document(text='input document') for _ in range(10)])
        )
    )[0]
    msg = Message(None, req, 'test', '123')
    return msg
