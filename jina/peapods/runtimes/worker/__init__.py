import argparse
import asyncio
import multiprocessing
import threading
from abc import ABC
from typing import Optional, Union, List

import grpc

from ..asyncio import AsyncNewLoopRuntime
from ..request_handlers.data_request_handler import (
    DataRequestHandler,
)
from ....proto import jina_pb2_grpc
from ....proto.jina_pb2 import ControlRequestProto
from ....types.request.control import ControlRequest
from ....types.request.data import DataRequest


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
        jina_pb2_grpc.add_JinaControlRequestRPCServicer_to_server(
            self, self._grpc_server
        )
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

        # 0.5 gives the runtime some time to complete outstanding responses
        # this should be handled better, 0.5 is a rather random number
        await self._grpc_server.stop(0.5)
        self.logger.debug('Stopped GRPC Server')

    async def async_teardown(self):
        """Close the data request handler"""
        await self.async_cancel()
        self._data_request_handler.close()

    async def process_data(self, requests: List[DataRequest], *args) -> DataRequest:
        """
        Process they received message and return the result as a new message

        :param requests: the data request to process
        :param args: additional arguments in the grpc call, ignored
        :returns: the response message
        """
        try:
            if self.logger.debug_enabled:
                self._log_data_request(requests[0])

            return self._data_request_handler.handle(requests=requests)
        except (RuntimeError, Exception) as ex:
            self.logger.error(
                f'{ex!r}' + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )

            requests[0].add_exception(ex, self._data_request_handler._executor)
            return requests[0]

    async def process_control(self, request: ControlRequest, *args) -> ControlRequest:
        """
        Process they received message and return the result as a new message

        :param request: the data request to process
        :param args: additional arguments in the grpc call, ignored
        :returns: the response message
        """
        try:
            if self.logger.debug_enabled:
                self._log_control_request(request)

            if request.command == 'STATUS':
                pass
            else:
                raise RuntimeError(
                    f'WorkerRuntime received unsupported ControlRequest command {request.command}'
                )
        except (RuntimeError, Exception) as ex:
            self.logger.error(
                f'{ex!r}' + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )

            request.add_exception(ex, self._data_request_handler._executor)
        return request
