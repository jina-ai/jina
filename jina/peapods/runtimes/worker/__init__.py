import argparse
import asyncio
import multiprocessing
import threading
from abc import ABC
from typing import Optional, Union, List

import grpc

from ..request_handlers.data_request_handler import (
    DataRequestHandler,
)
from ..asyncio import AsyncNewLoopRuntime
from ...networking import GrpcConnectionPool
from ....excepts import RuntimeTerminated
from ....proto import jina_pb2_grpc
from ....types.message import Message


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
        bind_addr = f'0.0.0.0:{self.args.port_in}'
        self._grpc_server.add_insecure_port(bind_addr)
        self.logger.debug(f'Start listening on {bind_addr}')
        await self._grpc_server.start()

    async def async_run_forever(self):
        """Block until the GRPC server is terminated """
        await self._grpc_server.wait_for_termination()

    async def async_cancel(self):
        """Stop the GRPC server"""
        self.logger.debug('Cancel WorkerRuntime')

        await self._grpc_server.stop(0)
        self.logger.debug('Stopped GRPC Server')

    async def async_teardown(self):
        """Close the data request handler"""
        await self.async_cancel()
        self._data_request_handler.close()

    async def Call(self, messages: List[Message], *args) -> Message:
        """
        Process they received message and return the result as a new message

        :param messages: the messages to process
        :param args: additional arguments in the grpc call, ignored
        :returns: the response message
        """
        try:
            return self._handle(messages)
        except RuntimeTerminated:
            self._cancel()
        except (RuntimeError, Exception) as ex:
            self.logger.error(
                f'{ex!r}' + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )
            raise

    def _handle(self, messages: List[Message]) -> Message:
        """Process the given message, data requests are passed to the DataRequestHandler

        :param messages: received messages
        :return: the transformed message.
        """

        # messages have to all be of the same type (DataRequest/ControlRequest)
        # we can check the first to find their type
        # DataRequests are handled en bloc, ControlRequests one by one
        if messages[0].envelope.request_type != 'DataRequest':
            return self._handle_control_requests(messages)
        else:
            if self.logger.debug_enabled:
                self._log_info_messages(messages)

            return self._data_request_handler.handle(messages=messages)

    def _handle_control_requests(self, messages):
        # responses for ControlRequests dont matter, just return the last ControlRequest back to the caller
        last_message = None
        for msg in messages:
            if self.logger.debug_enabled:
                self._log_info_msg(msg)

            if msg.request.command == 'TERMINATE':
                raise RuntimeTerminated()
            elif msg.request.command == 'STATUS':
                pass
            else:
                raise RuntimeError(
                    f'WorkerRuntime received unsupported ControlRequest command {msg.request.command}'
                )
            last_message = msg
        return last_message

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
