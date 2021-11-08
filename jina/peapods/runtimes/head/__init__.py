import argparse
import asyncio
import multiprocessing
import threading
import time
from abc import ABC
from typing import Optional, Union

import grpc
from grpc import RpcError

from ..zmq.asyncio import AsyncNewLoopRuntime
from ...networking import GrpcConnectionPool
from ....excepts import RuntimeTerminated
from ....proto import jina_pb2_grpc
from ....types.message import Message
from ....types.message.common import ControlMessage


class HeadRuntime(AsyncNewLoopRuntime, ABC):
    def __init__(
        self,
        args: argparse.Namespace,
        connection_pool: GrpcConnectionPool,
        cancel_event: Optional[
            Union['asyncio.Event', 'multiprocessing.Event', 'threading.Event']
        ] = None,
        **kwargs,
    ):
        """Initialize grpc server for the head runtime.
        :param args: args from CLI
        :param connection_pool: ConnectionPool to use for sending messages
        :param cancel_event: the cancel event used to wait for canceling
        :param kwargs: keyword args
        """
        super().__init__(args, cancel_event, **kwargs)

        self.connection_pool = connection_pool
        self.uses_before_address = args.uses_before_address
        if self.uses_before_address:
            self.connection_pool.add_connection(
                pod='uses_before', address=self.uses_before_address
            )
        self.uses_after_address = args.uses_after_address
        if self.uses_after_address:
            self.connection_pool.add_connection(
                pod='uses_after', address=self.uses_after_address
            )

    async def async_setup(self):
        """ Wait for the GRPC server to start """
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
        self.logger.debug('Cancel HeadRuntime')

        await self._grpc_server.stop(0)

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
        :param shutdown_event: the multiprocessing event to detect if the process failed
        :param ctrl_address: the address where the control message needs to be sent
        :param kwargs: extra keyword arguments
        :return: True if is ready or it needs to be shutdown
        """
        timeout_ns = 1000000000 * timeout if timeout else None
        now = time.time_ns()
        while timeout_ns is None or time.time_ns() - now < timeout_ns:
            if shutdown_event.is_set() or HeadRuntime.is_ready(ctrl_address):
                return True
            time.sleep(0.1)

        return False

    async def Call(self, msg, *args) -> Message:
        """ Process they received message and return the result as a new message

        :param msg: the message to process
        :param args: additional arguments in the grpc call, ignored
        :returns: the response message
        """
        try:
            return self._handle(msg)
        except RuntimeTerminated:
            HeadRuntime.cancel(self.is_cancel)
        except (RuntimeError, Exception) as ex:
            self.logger.error(
                f'{ex!r}' + f'\n add "--quiet-error" to suppress the exception details'
                if not self.args.quiet_error
                else '',
                exc_info=not self.args.quiet_error,
            )
            raise

    def _handle(self, msg: Message) -> Message:
        if self.logger.debug_enabled:
            self._log_info_msg(msg)

        # skip executor for non-DataRequest
        if msg.envelope.request_type != 'DataRequest':
            if msg.request.command == 'TERMINATE':
                raise RuntimeTerminated()
            elif msg.request.command == 'ACTIVATE':
                # TODO handle registering peas
                pass
            elif msg.request.command == 'DEACTIVATE':
                # TODO handle removing peas
                pass
            return msg

        # TODO here needs to go the multi message handling: receive multi message from the gateway, feed to uses_before/workers and handlo also their multi message
        # send to uses_before
        if self.uses_before_address:
            msg = await asyncio.gather(
                self.connection_pool.send_message(msg=msg, pod='uses_before')
            )
        # send to workers
        msg = await asyncio.gather(
            self.connection_pool.send_message(msg=msg, pod='worker')
        )
        # send to uses_after
        if self.uses_after_address:
            msg = await asyncio.gather(
                self.connection_pool.send_message(msg=msg, pod='uses_after')
            )

        return msg
