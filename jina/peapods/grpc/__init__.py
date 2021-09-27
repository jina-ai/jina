import argparse
import asyncio
from typing import Optional, Callable

import grpc
from google.protobuf import struct_pb2

from jina.logging.logger import JinaLogger
from jina.peapods.networking import create_connection_pool

from jina.proto import jina_pb2_grpc, jina_pb2
from jina.types.message import Message
from jina.types.message.common import ControlMessage
from jina.types.routing.table import RoutingTable


class Grpclet(jina_pb2_grpc.JinaDataRequestRPCServicer):
    """A `Grpclet` object can send/receive Messages via gRPC.

    :param args: the parsed arguments from the CLI
    :param message_callback: the callback to call on received messages
    :param logger: the logger to use
    """

    def __init__(
        self,
        args: argparse.Namespace,
        message_callback: Callable[['Message'], None],
        logger: Optional['JinaLogger'] = None,
    ):
        self.args = args
        self._logger = logger or JinaLogger(self.__class__.__name__)
        self.callback = message_callback

        self._connection_pool = create_connection_pool(args)

        self.msg_recv = 0
        self.msg_sent = 0
        self._pending_tasks = []
        self._static_routing_table = args.static_routing_table
        if args.static_routing_table:
            self._routing_table = RoutingTable(args.routing_table)
            self._next_targets = self._routing_table.get_next_target_addresses()
        else:
            self._routing_table = None
            self._next_targets = None

    async def send_message(self, msg: 'Message', **kwargs):
        """
        Sends a message via gRPC to the target indicated in the message's routing table
        :param msg: the protobuf message to send
        :param kwargs: Additional arguments.
        """

        if self._next_targets:
            for pod_address in self._next_targets:
                self._send_message(msg, pod_address)
        else:
            routing_table = RoutingTable(msg.envelope.routing_table)
            next_targets = routing_table.get_next_targets()
            for target, _ in next_targets:
                self._send_message(
                    self._add_envelope(msg, target),
                    target.active_target_pod.full_address,
                )

    def _send_message(self, msg, pod_address):
        try:
            self.msg_sent += 1

            self._pending_tasks.append(
                self._connection_pool.send_message(msg, pod_address)
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

    async def close(self, grace_period=None, *args, **kwargs):
        """Stop the Grpc server
        :param grace_period: Time to wait for message processing to finish before killing the grpc server
        :param args: Extra positional arguments
        :param kwargs: Extra key-value arguments
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
        self._logger.debug('Close grpc server')
        await self._grpc_server.stop(grace_period)

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
        bind_addr = f'{self.args.host}:{self.args.port_in}'
        self._grpc_server.add_insecure_port(bind_addr)
        self._logger.debug(f'Binding gRPC server for data requests to {bind_addr}')
        self._connection_pool.start()
        await self._grpc_server.start()
        await self._grpc_server.wait_for_termination()

    def _update_pending_tasks(self):
        self._pending_tasks = [task for task in self._pending_tasks if not task.done()]

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
