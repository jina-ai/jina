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
    runtime = GRPCDataRuntime(args)
    runtime._data_request_handler.handle = mocker.Mock()

    runtime_thread = Thread(target=runtime.run_forever)
    runtime_thread.start()

    assert runtime.wait_for_ready_or_shutdown(
        timeout=5.0, ctrl_address=f'{args.host}:{args.port_in}', shutdown_event=Event()
    )
    Grpclet._create_grpc_stub(f'{args.host}:{args.port_in}', is_async=False).Call(
        _create_test_data_message()
    )
    time.sleep(0.1)
    runtime._data_request_handler.handle.assert_called()

    runtime.cancel(f'{args.host}:{args.port_in}')
    assert not runtime.is_ready(f'{args.host}:{args.port_in}')


def _create_test_data_message():
    req = list(
        request_generator(
            '/', DocumentArray([Document(text='input document') for _ in range(10)])
        )
    )[0]
    msg = Message(None, req, 'test', '123')
    return msg
