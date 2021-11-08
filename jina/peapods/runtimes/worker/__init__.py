import argparse
import asyncio
import multiprocessing
import threading
import time
from abc import ABC
from typing import Optional, Union

import grpc
from grpc import RpcError

from ..request_handlers.data_request_handler import (
    DataRequestHandler,
)
from ..zmq.asyncio import AsyncNewLoopRuntime
from ...networking import GrpcConnectionPool
from ....excepts import RuntimeTerminated
from ....proto import jina_pb2_grpc
from ....types.message import Message
from ....types.message.common import ControlMessage


class WorkerRuntime(AsyncNewLoopRuntime, ABC):
    """Runtime procedure leveraging :class:`Grpclet` for sending DataRequests"""

    def __init__(
        self,
        args: argparse.Namespace,
        cancel_event: Optional[
            Union['asyncio.Event', 'multiprocessing.Event', 'threading.Event']
        ] = None,
        **kwargs,
    ):
        """Initialize grpc and data request handling.
        :param args: args from CLI
        :param cancel_event: the cancel event used to wait for canceling
        :param kwargs: keyword args
        """
        super().__init__(args, cancel_event, **kwargs)

        # Keep this initialization order, otherwise readiness check is not valid
        self._data_request_handler = DataRequestHandler(args, self.logger)

    async def async_setup(self):
        """
        Wait for the GRPC server to start
        """
        self._grpc_server = grpc.aio.server(
            options=[
                ('grpc.max_send_message_length', -1),
                ('grpc.max_receive_message_length', -1),
            ]
        )

        jina_pb2_grpc.add_JinaDataRequestRPCServicer_to_server(self, self._grpc_server)
        self._grpc_server.add_insecure_port(f'0.0.0.0:{self.args.port_in}')
        await self._grpc_server.start()

    async def async_run_forever(self):
        """Block until the GRPC server is terminated """
        await self._grpc_server.wait_for_termination()

    async def async_cancel(self):
        """Stop the GRPC server"""
        self.logger.debug('Cancel WorkerRuntime')

        await self._grpc_server.stop(0)

    async def async_teardown(self):
        """Close the data request handler"""
        self._data_request_handler.close()

    @staticmethod
    def is_ready(ctrl_address: str, **kwargs) -> bool:
        """
        Check if status is ready.

        :param ctrl_address: the address where the control message needs to be sent
        :param kwargs: extra keyword arguments

        :return: True if status is ready else False.
        """

        try:
            GrpcConnectionPool.send_message_sync(ControlMessage('STATUS'), ctrl_address)
        except RpcError:
            return False

        return True

    @staticmethod
    def wait_for_ready_or_shutdown(
        timeout: Optional[float],
        shutdown_event: Union[multiprocessing.Event, threading.Event],
        ctrl_address: str,
        **kwargs,
    ):
        """
        Check if the runtime has successfully started

        :param timeout: The time to wait before readiness or failure is determined
        :param ctrl_address: the address where the control message needs to be sent
        :param shutdown_event: the multiprocessing event to detect if the process failed
        :param kwargs: extra keyword arguments
        :return: True if is ready or it needs to be shutdown
        """
        timeout_ns = 1000000000 * timeout if timeout else None
        now = time.time_ns()
        while timeout_ns is None or time.time_ns() - now < timeout_ns:
            if shutdown_event.is_set() or WorkerRuntime.is_ready(ctrl_address):
                return True
            time.sleep(0.1)

        return False

    async def Call(self, msg, *args) -> Message:
        """
        Process they received message and return the result as a new message

        :param msg: the message to process
        :param args: additional arguments in the grpc call, ignored
        :returns: the response message
        """
        try:
            return self._handle(msg)
        except RuntimeTerminated:
            WorkerRuntime.cancel(self.is_cancel)
        except (RuntimeError, Exception) as ex:
            self.logger.error(
                f'{ex!r}' + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )
            raise

    def _handle(self, msg: Message) -> Message:
        """Process the given message, data requests are passed to the DataRequestHandler

        :param msg: received message
        :return: the transformed message.
        """

        if self.logger.debug_enabled:
            self._log_info_msg(msg)

        # skip executor for non-DataRequest
        if msg.envelope.request_type != 'DataRequest':
            if msg.request.command == 'TERMINATE':
                raise RuntimeTerminated()
            return msg

        self._data_request_handler.handle(msg=msg)
        return msg

    def _log_info_msg(self, msg):
        info_msg = f'recv {msg.envelope.request_type} '
        req_type = msg.envelope.request_type
        if req_type == 'DataRequest':
            info_msg += (
                f'({msg.envelope.header.exec_endpoint}) - ({msg.envelope.request_id}) '
            )
        elif req_type == 'ControlRequest':
            info_msg += f'({msg.request.command}) '
        self.logger.debug(info_msg)
