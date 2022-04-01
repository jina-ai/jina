import argparse
import asyncio
import multiprocessing
import threading
from abc import ABC
from typing import List, Optional, Union

import grpc

from jina.proto import jina_pb2_grpc
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.request_handlers.data_request_handler import DataRequestHandler
from jina.types.request.control import ControlRequest
from jina.types.request.data import DataRequest


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

    async def async_setup(self):
        """
        Start the DataRequestHandler and wait for the GRPC server to start
        """

        # Keep this initialization order
        # otherwise readiness check is not valid
        # The DataRequestHandler needs to be started BEFORE the grpc server
        self._data_request_handler = DataRequestHandler(self.args, self.logger)

        self._grpc_server = grpc.aio.server(
            options=[
                ('grpc.max_send_message_length', -1),
                ('grpc.max_receive_message_length', -1),
            ]
        )

        jina_pb2_grpc.add_JinaSingleDataRequestRPCServicer_to_server(
            self, self._grpc_server
        )
        jina_pb2_grpc.add_JinaDataRequestRPCServicer_to_server(self, self._grpc_server)
        jina_pb2_grpc.add_JinaControlRequestRPCServicer_to_server(
            self, self._grpc_server
        )
        bind_addr = f'0.0.0.0:{self.args.port}'
        self.logger.debug(f'Start listening on {bind_addr}')
        self._grpc_server.add_insecure_port(bind_addr)
        await self._grpc_server.start()

    async def async_run_forever(self):
        """Block until the GRPC server is terminated"""
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

    async def process_single_data(self, request: DataRequest, context) -> DataRequest:
        """
        Process the received requests and return the result as a new request

        :param request: the data request to process
        :param context: grpc context
        :returns: the response request
        """
        return await self.process_data([request], context)

    async def process_data(self, requests: List[DataRequest], context) -> DataRequest:
        """
        Process the received requests and return the result as a new request

        :param requests: the data requests to process
        :param context: grpc context
        :returns: the response request
        """
        try:
            if self.logger.debug_enabled:
                self._log_data_request(requests[0])

            return await self._data_request_handler.handle(requests=requests)
        except (RuntimeError, Exception) as ex:
            self.logger.error(
                f'{ex!r}' + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )

            requests[0].add_exception(ex, self._data_request_handler._executor)
            context.set_trailing_metadata((('is-error', 'true'),))
            return requests[0]

    async def process_control(self, request: ControlRequest, *args) -> ControlRequest:
        """
        Process the received control request and return the same request

        :param request: the control request to process
        :param args: additional arguments in the grpc call, ignored
        :returns: the input request
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
