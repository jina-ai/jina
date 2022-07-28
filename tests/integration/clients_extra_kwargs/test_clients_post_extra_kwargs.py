import os

import grpc
import pytest

from jina import Flow, __default_host__
from jina.clients import Client
from jina.excepts import PortAlreadyUsed
from jina.helper import is_port_free
from jina.serve.runtimes.gateway.grpc import GRPCGatewayRuntime as _GRPCGatewayRuntime
from tests import random_docs


@pytest.fixture(scope='function')
def flow_with_grpc(monkeypatch):
    class AuthInterceptor(grpc.aio.ServerInterceptor):
        def __init__(self, key):
            self._valid_metadata = ('rpc-auth-header', key)

            def deny(_, context):
                context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Invalid key')

            self._deny = grpc.unary_unary_rpc_method_handler(deny)

        async def intercept_service(self, continuation, handler_call_details):
            meta = handler_call_details.invocation_metadata

            metas_dicts = {m.key: m.value for m in meta}
            assert 'rpc-auth-header' in metas_dicts
            assert (
                metas_dicts['rpc-auth-header'] == 'access_key'
            ), f'Invalid access key detected, got {metas_dicts["rpc-auth-header"]}'

            for m in meta:
                if m == self._valid_metadata:
                    return await continuation(handler_call_details)

            return self._deny

    class AlternativeGRPCGatewayRuntime(_GRPCGatewayRuntime):
        async def async_setup(self):
            """
            The async method to setup.
            Create the gRPC server and expose the port for communication.
            """
            if not self.args.proxy and os.name != 'nt':
                os.unsetenv('http_proxy')
                os.unsetenv('https_proxy')

            if not (is_port_free(__default_host__, self.args.port)):
                raise PortAlreadyUsed(f'port:{self.args.port}')

            self.server = grpc.aio.server(
                interceptors=(AuthInterceptor('access_key'),),
                options=[
                    ('grpc.max_send_message_length', -1),
                    ('grpc.max_receive_message_length', -1),
                ],
            )


            await self._async_setup_server()

    monkeypatch.setattr(
        'jina.serve.runtimes.gateway.grpc.GRPCGatewayRuntime',
        AlternativeGRPCGatewayRuntime,
    )
    return Flow(protocol='grpc').add()


def test_client_grpc_kwargs(flow_with_grpc):
    with flow_with_grpc:
        client = Client(
            port=flow_with_grpc.port,
            host='localhost',
            protocol='grpc',
        )

        meta_data = (('rpc-auth-header', 'invalid_access_key'),)

        try:
            client.post('', random_docs(1), request_size=1, metadata=meta_data)
        except Exception as exc:
            assert 'Invalid access key detected, got invalid_access_key' in repr(exc)
