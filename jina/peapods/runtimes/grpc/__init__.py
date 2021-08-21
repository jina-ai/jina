import argparse
import asyncio
import multiprocessing
import threading
import time
from abc import ABC
from collections import defaultdict
from typing import Optional, Union, Dict, List

from grpc import RpcError

from jina.enums import OnErrorStrategy
from jina.excepts import NoExplicitMessage, ChainedPodException, RuntimeTerminated
from jina.helper import get_or_reuse_loop, random_identity
from jina.peapods.grpc import Grpclet
from jina.peapods.runtimes.base import BaseRuntime
from jina.peapods.runtimes.request_handlers.data_request_handler import (
    DataRequestHandler,
)
from jina.proto import jina_pb2
from jina.types.message import Message
from jina.types.routing.table import RoutingTable


class GRPCDataRuntime(BaseRuntime, ABC):
    """Runtime procedure leveraging :class:`Grpclet` for sending DataRequests"""

    def __init__(self, args: argparse.Namespace, **kwargs):
        """Initialize grpc and data request handling.
        :param args: args from CLI
        :param kwargs: extra keyword arguments
        """
        super().__init__(args, **kwargs)
        self._id = random_identity()
        self._loop = get_or_reuse_loop()
        self._last_active_time = time.perf_counter()

        self._pending_msgs = defaultdict(list)  # type: Dict[str, List[Message]]
        self._partial_requests = None
        self._pending_tasks = []
        self._static_routing_table = hasattr(args, 'routing_table')

        self._data_request_handler = DataRequestHandler(args, self.logger)
        self._grpclet = Grpclet(
            args=self.args,
            message_callback=self._callback,
            logger=self.logger,
        )

    def _update_pending_tasks(self):
        self._pending_tasks = [task for task in self._pending_tasks if not task.done()]

    def run_forever(self):
        """Start the `Grpclet`."""
        self._grpclet_task = self._loop.create_task(self._grpclet.start())
        self._loop.run_until_complete(self._grpclet_task)

    def teardown(self):
        """Close the `Grpclet` and `DataRequestHandler`."""
        self.logger.debug('Teardown GRPCDataRuntime')

        self._data_request_handler.close()
        start = time.time()
        while self._pending_tasks and time.time() - start < 1.0:
            self._update_pending_tasks()
            time.sleep(0.1)
        self._loop.stop()
        self._loop.close()

        super().teardown()

    async def _close_grpclet(self):
        await self._grpclet.close()
        self._grpclet_task.cancel()

    @staticmethod
    def get_control_address(**kwargs):
        """
        Does return None, exists for keeping interface compatible with ZEDRuntime

        :param kwargs: extra keyword arguments
        :returns: None
        """
        return None

    @staticmethod
    def is_ready(ctrl_address: str, **kwargs) -> bool:
        """
        Check if status is ready.

        :param ctrl_address: the address where the control message needs to be sent
        :param kwargs: extra keyword arguments

        :return: True if status is ready else False.
        """

        try:
            response = Grpclet.send_ctrl_msg(ctrl_address, 'STATUS')
        except RpcError:
            return False

        return True

    @staticmethod
    def activate(
        **kwargs,
    ):
        """
        Does nothing
        :param kwargs: extra keyword arguments
        """
        pass

    @staticmethod
    def cancel(
        control_address: str,
        **kwargs,
    ):
        """
        Cancel this runtime by sending a TERMINATE control message

        :param control_address: the address where the control message needs to be sent
        :param kwargs: extra keyword arguments
        """
        Grpclet.send_ctrl_msg(control_address, 'TERMINATE')

    @staticmethod
    def wait_for_ready_or_shutdown(
        timeout: Optional[float],
        ctrl_address: str,
        shutdown_event: Union[multiprocessing.Event, threading.Event],
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
            if shutdown_event.is_set() or GRPCDataRuntime.is_ready(ctrl_address):
                return True
            time.sleep(0.1)

        return False

    async def _callback(self, msg: Message) -> None:
        try:
            msg = self._post_hook(self._handle(self._pre_hook(msg)))
            if msg.is_data_request:
                asyncio.create_task(self._grpclet.send_message(msg))
        except RuntimeTerminated:
            # this is the proper way to end when a terminate signal is sent
            self._pending_tasks.append(asyncio.create_task(self._close_grpclet()))
        except KeyboardInterrupt as kbex:
            self.logger.debug(f'{kbex!r} causes the breaking from the event loop')
            self._pending_tasks.append(asyncio.create_task(self._close_grpclet()))
        except (SystemError) as ex:
            # save executor
            self.logger.debug(f'{ex!r} causes the breaking from the event loop')
            self._pending_tasks.append(asyncio.create_task(self._close_grpclet()))
        except NoExplicitMessage:
            # silent and do not propagate message anymore
            # 1. wait partial message to be finished
            pass
        except (RuntimeError, Exception, ChainedPodException) as ex:
            if self.args.on_error_strategy == OnErrorStrategy.THROW_EARLY:
                raise
            if isinstance(ex, ChainedPodException):
                # the error is print from previous pod, no need to show it again
                # hence just add exception and propagate further
                # please do NOT add logger.error here!
                msg.add_exception()
            else:
                msg.add_exception(ex, executor=self._data_request_handler._executor)
                self.logger.error(
                    f'{ex!r}'
                    + f'\n add "--quiet-error" to suppress the exception details'
                    if not self.args.quiet_error
                    else '',
                    exc_info=not self.args.quiet_error,
                )

            if msg.is_data_request:
                asyncio.create_task(self._grpclet.send_message(msg))
            asyncio.create_task(self._grpclet.send_message(msg))

    def _handle(self, msg: Message) -> Message:
        """Register the current message to this pea, so that all message-related properties are up-to-date, including
        :attr:`request`, :attr:`prev_requests`, :attr:`message`, :attr:`prev_messages`. And then call the executor to handle
        this message if its envelope's  status is not ERROR, else skip handling of message.
        .. note::
            Handle does not handle explicitly message because it may wait for different messages when different parts are expected
        :param msg: received message
        :return: the transformed message.
        """

        # skip executor for non-DataRequest
        if msg.envelope.request_type != 'DataRequest':
            if msg.request.command == 'TERMINATE':
                raise RuntimeTerminated()
            self.logger.debug(f'skip executor: not data request')
            return msg

        req_id = msg.envelope.request_id
        num_expected_parts = self._get_expected_parts(msg)
        self._data_request_handler.handle(
            msg=msg,
            partial_requests=[m.request for m in self._pending_msgs[req_id]]
            if num_expected_parts > 1
            else None,
            peapod_name=self.name,
        )

        return msg

    def _get_expected_parts(self, msg):
        if msg.is_data_request:
            if not self._static_routing_table:
                graph = RoutingTable(msg.envelope.routing_table)
                return graph.active_target_pod.expected_parts
            else:
                return self.args.num_part
        else:
            return 1

    def _pre_hook(self, msg: Message) -> Message:
        """
        Pre-hook function, what to do after first receiving the message.
        :param msg: received message
        :return: `Message`
        """
        msg.add_route(self.name, self._id)

        expected_parts = self._get_expected_parts(msg)

        req_id = msg.envelope.request_id
        if expected_parts > 1:
            self._pending_msgs[req_id].append(msg)

        num_partial_requests = len(self._pending_msgs[req_id])

        if self.logger.debug_enabled:
            self._log_info_msg(
                msg,
                f'({num_partial_requests}/{expected_parts} parts)'
                if expected_parts > 1
                else '',
            )

        if expected_parts > 1 and expected_parts > num_partial_requests:
            # NOTE: reduce priority is higher than chain exception
            # otherwise a reducer will lose its function when earlier pods raise exception
            raise NoExplicitMessage

        if (
            msg.envelope.status.code == jina_pb2.StatusProto.ERROR
            and self.args.on_error_strategy >= OnErrorStrategy.SKIP_HANDLE
        ):
            raise ChainedPodException

        return msg

    def _log_info_msg(self, msg, part_str):
        info_msg = f'recv {msg.envelope.request_type} '
        req_type = msg.envelope.request_type
        if req_type == 'DataRequest':
            info_msg += (
                f'({msg.envelope.header.exec_endpoint}) - ({msg.envelope.request_id}) '
            )
        elif req_type == 'ControlRequest':
            info_msg += f'({msg.request.command}) '
        info_msg += f'{part_str} from {msg.colored_route}'
        self.logger.debug(info_msg)

    def _post_hook(self, msg: Message) -> Message:
        """
        Post-hook function, what to do before handing out the message.
        :param msg: the transformed message
        :return: `Message`
        """
        # do NOT access `msg.request.*` in the _pre_hook, as it will trigger the deserialization
        # all meta information should be stored and accessed via `msg.envelope`

        self._last_active_time = time.perf_counter()

        if self._get_expected_parts(msg) > 1:
            msgs = self._pending_msgs.pop(msg.envelope.request_id)
            msg.merge_envelope_from(msgs)

        msg.update_timestamp()
        return msg
