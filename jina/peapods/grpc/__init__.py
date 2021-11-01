import argparse
import asyncio
from typing import Optional, Callable

import grpc
from google.protobuf import struct_pb2

from jina.enums import PollingType
from jina.logging.logger import JinaLogger
from jina.peapods.networking import create_connection_pool, ConnectionPool

from jina.proto import jina_pb2_grpc, jina_pb2
from jina.types.message import Message
from jina.types.message.common import ControlMessage
from jina.types.routing.table import RoutingTable


class Grpclet(jina_pb2_grpc.JinaDataRequestRPCServicer):
    """A `Grpclet` object can send/receive Messages via gRPC.

    :param port: port to listen on
    :param connection_pool: connection_pool to use for sending
    :param host: host to bind to, defaults to 0.0.0.0
    :param message_callback: the callback to call on received messages
    :param logger: the logger to use
    """

    def __init__(
        self,
        port: int,
        connection_pool: ConnectionPool,
        host: str = '0.0.0.0',
        message_callback: Callable[['Message'], None] = None,
        logger: Optional['JinaLogger'] = None,
    ):
        self.host = host
        self.port = port
        self._logger = logger or JinaLogger(self.__class__.__name__)
        self.callback = message_callback

        self._connection_pool = connection_pool

        self.msg_recv = 0
        self.msg_sent = 0
        self._pending_tasks = []

    async def send_message(
        self, msg: 'Message', target_address: str, polling_type: PollingType, **kwargs
    ):
        """
        Sends a message via gRPC to the target indicated in the message's routing table
        :param msg: the protobuf message to send
        :param target_address: address to send to, should include the port like 1.1.1.1:53
         :param polling_type: polling type can be any or all
        :param kwargs: Additional arguments.
        """
        try:
            self.msg_sent += 1

            self._pending_tasks.append(
                self._connection_pool.send_message(msg, target_address, polling_type)
            )

            self._update_pending_tasks()
        except grpc.RpcError as ex:
            self._logger.error('Sending data request via grpc failed', ex)
            raise ex

    @staticmethod
    def send_ctrl_msg(pod_address: str, command: str, timeout=1.0):
        """
        Sends a control message via gRPC to pod_address
        :param pod_address: the pod to send the command to
        :param command: the command to send (TERMINATE/ACTIVATE/...)
        :param timeout: optional timeout for the request in seconds
        :returns: Empty protobuf struct
        """
        stub = Grpclet._create_grpc_stub(pod_address, is_async=False)
        response = stub.Call(ControlMessage(command), timeout=timeout)
        return response

    @staticmethod
    def _create_grpc_stub(pod_address, is_async=True):
        if is_async:
            channel = grpc.aio.insecure_channel(
                pod_address,
                options=[
                    ('grpc.max_send_message_length', -1),
                    ('grpc.max_receive_message_length', -1),
                ],
            )
        else:
            channel = grpc.insecure_channel(
                pod_address,
                options=[
                    ('grpc.max_send_message_length', -1),
                    ('grpc.max_receive_message_length', -1),
                ],
            )

        stub = jina_pb2_grpc.JinaDataRequestRPCStub(channel)

        return stub

    def _add_envelope(self, msg, routing_table):
        if not self._static_routing_table:
            new_envelope = jina_pb2.EnvelopeProto()
            new_envelope.CopyFrom(msg.envelope)
            new_envelope.routing_table.CopyFrom(routing_table.proto)
            new_message = Message(request=msg.request, envelope=new_envelope)

            return new_message
        else:
            return msg

    async def stop_receiving(self, grace_period=None):
        """Stop accepting new messages
        :param grace_period: Time to wait for message processing to finish before killing the grpc server
        """
        self._logger.debug('Close grpc server')
        await self._grpc_server.stop(grace_period)

    async def close(self, grace_period=None, *args, **kwargs):
        """Stop the Grpc server
        :param grace_period: Time to wait for message processing to finish before killing the grpc server
        :param args: Extra positional arguments
        :param kwargs: Extra key-value arguments
        """
        await self.stop_receiving(grace_period)
        await self.stop_sending()

    async def stop_sending(self):
        """
        Flush pending messages and stop sending new messages
        """
        self._update_pending_tasks()
        try:
            await asyncio.wait_for(asyncio.gather(*self._pending_tasks), timeout=1.0)
        except asyncio.TimeoutError:
            self._update_pending_tasks()
            self._logger.warning(
                f'Could not gracefully complete {len(self._pending_tasks)} pending tasks on close.'
            )
        self._connection_pool.close()

    async def start(self):
        """
        Starts this Grpclet by starting its gRPC server
        """
        self._grpc_server = grpc.aio.server(
            options=[
                ('grpc.max_send_message_length', -1),
                ('grpc.max_receive_message_length', -1),
            ]
        )

        jina_pb2_grpc.add_JinaDataRequestRPCServicer_to_server(self, self._grpc_server)
        bind_addr = f'{self.host}:{self.port}'
        self._grpc_server.add_insecure_port(bind_addr)
        self._logger.debug(f'Binding gRPC server for data requests to {bind_addr}')
        self._connection_pool.start()
        await self._grpc_server.start()
        await self._grpc_server.wait_for_termination()

    def _update_pending_tasks(self):
        self._pending_tasks = [
            task for task in self._pending_tasks if task and not task.done()
        ]

    async def Call(self, msg, *args):
        """Processes messages received by the GRPC server
        :param msg: The received message
        :param args: Extra positional arguments
        :return: Empty protobuf struct, necessary to return for protobuf Empty
        """
        if self.callback:
            self._pending_tasks.append(asyncio.create_task(self.callback(msg)))
        else:
            self._logger.debug(
                'Grpclet received data request, but no callback was registered'
            )

        self.msg_recv += 1
        self._update_pending_tasks()
        return struct_pb2.Value()
