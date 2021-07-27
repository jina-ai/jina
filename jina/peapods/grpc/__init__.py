import inspect
from typing import Optional, Callable

import grpc
from google.protobuf import struct_pb2

from jina.helper import get_or_reuse_loop
from jina.proto import jina_pb2_grpc, jina_pb2
from jina.types.message import Message
from jina.types.routing.table import RoutingTable


class Grpclet(jina_pb2_grpc.JinaDataRequestRPCServicer):
    """A `Grpclet` object can send/receive DataRequests via gRPC.

    :param args: the parsed arguments from the CLI
    :param args: the callback to call on received messages
    :param logger: the logger to use
    """

    def __init__(
        self,
        args: 'argparse.Namespace',
        message_callback: Callable[['Message'], 'Message'],
        logger: Optional['JinaLogger'] = None,
    ):
        self.args = args
        self._stubs = {}
        self._logger = logger
        self._callback = message_callback
        self._loop = get_or_reuse_loop()

    def _get_dynamic_next_routes(self, message):
        routing_table = RoutingTable(message.envelope.routing_table)
        next_targets = routing_table.get_next_targets()
        next_routes = []
        for target, send_as_bind in next_targets:
            pod_address = target.active_target_pod.full_address
            if send_as_bind:
                raise ValueError(
                    f'Grpclet can not send as bind to target {pod_address}'
                )

            self.logger.debug(f'gonna send msg from {self.name} to {target.active_pod}')

            next_routes.append(target)
        return next_routes

    async def send_message(self, msg: 'Message', **kwargs):
        print(f'got this routing table {msg.envelope.routing_table}')
        routing_table = RoutingTable(msg.envelope.routing_table)
        next_targets = routing_table.get_next_targets()

        for target, send_as_bind in next_targets:
            pod_address = target.active_target_pod.full_address
            if send_as_bind:
                raise ValueError(
                    f'Grpclet can not send as bind to target {pod_address}'
                )
            self._logger.debug(f'send the following routing table {routing_table}')

            new_message = await self._add_envelope(msg, target)
            self._logger.debug(
                f'gonna send msg from {self.args.name} to {target.active_pod} at {pod_address}'
            )

            if pod_address not in self._stubs:
                await self._create_grpc_stub(pod_address)

            try:
                self._logger.debug(
                    f'send new message from {routing_table.active_pod} to {target.active_target_pod}'
                )
                bla = await self._stubs[pod_address].Call(new_message)
                print(bla)
            except grpc.RpcError as ex:
                self._logger.error('Sending data request via grpc failed', ex)
                raise ex

    async def _create_grpc_stub(self, pod_address):
        stub = jina_pb2_grpc.JinaDataRequestRPCStub(
            grpc.aio.insecure_channel(
                pod_address,
                options=[
                    ('grpc.max_send_message_length', -1),
                    ('grpc.max_receive_message_length', -1),
                ],
            )
        )
        self._stubs[pod_address] = stub

    async def _add_envelope(self, msg, routing_table):
        new_envelope = jina_pb2.EnvelopeProto()
        new_envelope.CopyFrom(msg.envelope)
        new_envelope.routing_table.CopyFrom(routing_table.proto)
        new_message = Message(request=msg.request, envelope=new_envelope)

        return new_message

    async def close(self, *args, **kwargs):
        await self._grpc_server.stop(grace=True)

    def run_forever(self):
        """The async running of server."""
        self._logger.debug('run forever')
        self._loop.run_until_complete(self._async_setup())
        self._loop.close()

    async def _async_setup(self):
        self._logger.debug('_async_setup')
        self._grpc_server = grpc.aio.server(
            options=[
                ('grpc.max_send_message_length', -1),
                ('grpc.max_receive_message_length', -1),
            ]
        )

        jina_pb2_grpc.add_JinaDataRequestRPCServicer_to_server(self, self._grpc_server)
        bind_addr = f'{self.args.host}:{self.args.port_in}'
        self._logger.debug('_buuh')
        self._grpc_server.add_insecure_port(bind_addr)
        self._logger.debug(f'Binding gRPC server for data requests to {bind_addr}')
        await self._grpc_server.start()
        self._logger.debug('started')
        await self._grpc_server.wait_for_termination()

    async def Call(self, msg, *args):
        if self._callback:
            self._logger.debug(
                f'Grpclet received data request calling callback {msg} cb {self._callback}'
            )
            if inspect.iscoroutinefunction(self._callback):
                await self._callback(msg)
            else:
                self._callback(msg)
        else:
            self._logger.debug(
                'Grpclet received data request, but no callback was registered'
            )

        self._logger.debug('Grpclet received data done')

        return struct_pb2.Value()
