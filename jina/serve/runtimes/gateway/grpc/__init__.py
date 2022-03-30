import os

import grpc

from jina import __default_host__
from jina.excepts import PortAlreadyUsed
from jina.helper import is_port_free
from jina.proto import jina_pb2_grpc
from jina.serve.runtimes.gateway import GatewayRuntime
from jina.serve.runtimes.gateway.request_handling import handle_request, handle_result
from jina.serve.stream import RequestStreamer

__all__ = ['GRPCGatewayRuntime']

from jina.types.request.control import ControlRequest


class GRPCGatewayRuntime(GatewayRuntime):
    """Gateway Runtime for gRPC."""

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
            options=[
                ('grpc.max_send_message_length', -1),
                ('grpc.max_receive_message_length', -1),
            ]
        )

        self._set_topology_graph()
        self._set_connection_pool()

        self.streamer = RequestStreamer(
            args=self.args,
            request_handler=handle_request(
                graph=self._topology_graph, connection_pool=self._connection_pool
            ),
            result_handler=handle_result,
        )

        self.streamer.Call = self.streamer.stream

        jina_pb2_grpc.add_JinaRPCServicer_to_server(self.streamer, self.server)
        jina_pb2_grpc.add_JinaControlRequestRPCServicer_to_server(self, self.server)
        bind_addr = f'{__default_host__}:{self.args.port}'

        if self.args.ssl_keyfile and self.args.ssl_certfile:
            with open(self.args.ssl_keyfile, 'rb') as f:
                private_key = f.read()
            with open(self.args.ssl_certfile, 'rb') as f:
                certificate_chain = f.read()

            server_credentials = grpc.ssl_server_credentials(
                (
                    (
                        private_key,
                        certificate_chain,
                    ),
                )
            )
            self.server.add_secure_port(bind_addr, server_credentials)
        elif (
            self.args.ssl_keyfile != self.args.ssl_certfile
        ):  # if we have only ssl_keyfile and not ssl_certfile or vice versa
            raise ValueError(
                f"you can't pass a ssl_keyfile without a ssl_certfile and vice versa"
            )
        else:
            self.server.add_insecure_port(bind_addr)
        self.logger.debug(f' Start server bound to {bind_addr}')
        await self.server.start()

    async def async_teardown(self):
        """Close the connection pool"""
        # usually async_cancel should already have been called, but then its a noop
        # if the runtime is stopped without a sigterm (e.g. as a context manager, this can happen)
        await self.async_cancel()
        await self._connection_pool.close()

    async def async_cancel(self):
        """The async method to stop server."""
        await self.server.stop(0)

    async def async_run_forever(self):
        """The async running of server."""
        self._connection_pool.start()
        await self.server.wait_for_termination()

    async def process_control(self, request: ControlRequest, *args) -> ControlRequest:
        """
        Should be used to check readiness by sending STATUS ControlRequests.
        Throws for any other command than STATUS.

        :param request: the ControlRequest, should have command 'STATUS'
        :param args: additional arguments in the grpc call, ignored
        :returns: will be the original request
        """

        if self.logger.debug_enabled:
            self._log_control_request(request)
        if request.command != 'STATUS':
            raise ValueError('Gateway only support STATUS ControlRequests')
        return request
