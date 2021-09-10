import argparse
import time
from collections import defaultdict
from typing import Dict, List, Optional, Union

import zmq


from .base import ZMQRuntime
from ..request_handlers.data_request_handler import DataRequestHandler
from ...zmq import ZmqStreamlet
from ....enums import OnErrorStrategy, SocketType
from ....excepts import (
    NoExplicitMessage,
    MemoryOverHighWatermark,
    ChainedPodException,
    RuntimeTerminated,
    UnknownControlCommand,
)
from ....helper import random_identity
from ....logging.profile import used_memory
from ....proto import jina_pb2
from ....types.message import Message
from ....types.routing.table import RoutingTable

if False:
    import multiprocessing
    import threading
    from ....logging.logger import JinaLogger


class ZEDRuntime(ZMQRuntime):
    """Runtime procedure leveraging :class:`ZmqStreamlet` for Executor."""

    def __init__(self, args: 'argparse.Namespace', **kwargs):
        """Initialize private parameters and execute private loading functions.

        :param args: args from CLI
        :param kwargs: extra keyword arguments
        """
        super().__init__(args, **kwargs)
        self._id = random_identity()
        self._last_active_time = time.perf_counter()
        self.ctrl_addr = self.get_control_address(args.host, args.port_ctrl)

        # all pending messages collected so far, key is the request id
        self._pending_msgs = defaultdict(list)  # type: Dict[str, List['Message']]

        # idle_dealer_ids only becomes non-None when it receives IDLE ControlRequest
        self._idle_dealer_ids = set()

        self._data_request_handler = DataRequestHandler(self.args, self.logger)
        self._static_routing_table = args.static_routing_table

        self._load_zmqstreamlet()

    def run_forever(self):
        """Start the `ZmqStreamlet`."""
        self._zmqstreamlet.start(self._msg_callback)

    def teardown(self):
        """Close the `ZmqStreamlet` and `Executor`."""
        self._zmqstreamlet.close()
        self._data_request_handler.close()
        super().teardown()

    #: Private methods required by :meth:`setup`

    def _load_zmqstreamlet(self):
        """Load ZMQStreamlet to this runtime."""
        # important: fix zmqstreamlet ctrl address to replace the the ctrl address generated in the main
        # process/thread
        self._zmqstreamlet = ZmqStreamlet(
            args=self.args,
            logger=self.logger,
            ctrl_addr=self.ctrl_addr,
        )

    #: Private methods required by :meth:`teardown`
    def _check_memory_watermark(self):
        """Check the memory watermark."""
        if used_memory() > self.args.memory_hwm > 0:
            raise MemoryOverHighWatermark

    #: Private methods required by run_forever
    def _pre_hook(self, msg: 'Message') -> 'Message':
        """
        Pre-hook function, what to do after first receiving the message.

        :param msg: received message
        :return: `ZEDRuntime`
        """
        msg.add_route(self.name, self._id)

        expected_parts = self._expect_parts(msg)

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

        if msg.envelope.request_type == 'ControlRequest':
            self._handle_control_req(msg)

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

    def _post_hook(self, msg: 'Message') -> 'Message':
        """
        Post-hook function, what to do before handing out the message.

        :param msg: the transformed message
        :return: `ZEDRuntime`
        """
        # do NOT access `msg.request.*` in the _pre_hook, as it will trigger the deserialization
        # all meta information should be stored and accessed via `msg.envelope`

        self._last_active_time = time.perf_counter()
        self._check_memory_watermark()

        if self._expect_parts(msg) > 1:
            msgs = self._pending_msgs.pop(msg.envelope.request_id)
            msg.merge_envelope_from(msgs)

        msg.update_timestamp()
        return msg

    @staticmethod
    def _parse_params(parameters: Dict, executor_name: str):
        parsed_params = parameters
        specific_parameters = parameters.get(executor_name, None)
        if specific_parameters:
            parsed_params.update(**specific_parameters)
        return parsed_params

    def _handle(self, msg: 'Message') -> 'Message':
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
            self.logger.debug(f'skip executor: not data request')
            return msg

        # migrated from the previously RouteDriver logic
        # set dealer id
        if self._idle_dealer_ids:
            dealer_id = self._idle_dealer_ids.pop()
            msg.envelope.receiver_id = dealer_id

            # when no available dealer, pause the pollin from upstream
            if not self._idle_dealer_ids:
                self._zmqstreamlet.pause_pollin()
            self.logger.debug(
                f'using route, set receiver_id: {msg.envelope.receiver_id}'
            )

        req_id = msg.envelope.request_id
        num_expected_parts = self._expect_parts(msg)
        self._data_request_handler.handle(
            msg=msg,
            partial_requests=[m.request for m in self._pending_msgs[req_id]]
            if num_expected_parts > 1
            else None,
            peapod_name=self.name,
        )

        return msg

    def _handle_control_req(self, msg: 'Message'):
        # migrated from previous ControlDriver logic
        if msg.request.command == 'TERMINATE':
            msg.envelope.status.code = jina_pb2.StatusProto.SUCCESS
            raise RuntimeTerminated
        elif msg.request.command == 'STATUS':
            msg.envelope.status.code = jina_pb2.StatusProto.READY
            msg.request.parameters = vars(self.args)
        elif msg.request.command == 'IDLE':
            self._idle_dealer_ids.add(msg.envelope.receiver_id)
            self._zmqstreamlet.resume_pollin()
            self.logger.debug(
                f'{msg.envelope.receiver_id} is idle, now I know these idle peas {self._idle_dealer_ids}'
            )
        elif msg.request.command == 'CANCEL':
            if msg.envelope.receiver_id in self._idle_dealer_ids:
                self._idle_dealer_ids.remove(msg.envelope.receiver_id)
        elif msg.request.command == 'ACTIVATE':
            self._zmqstreamlet._send_idle_to_router()
        elif msg.request.command == 'DEACTIVATE':
            self._zmqstreamlet._send_cancel_to_router()
        else:
            raise UnknownControlCommand(
                f'don\'t know how to handle {msg.request.command}'
            )

    def _callback(self, msg: 'Message'):
        self.is_post_hook_done = False  #: if the post_hook is called
        msg = self._post_hook(self._handle(self._pre_hook(msg)))
        self.is_post_hook_done = True
        return msg

    def _msg_callback(self, msg: 'Message') -> None:
        """
        Callback function after receiving the message
        When nothing is returned then nothing is send out via :attr:`zmqlet.sock_out`.

        :param msg: received message
        """
        try:
            # notice how executor related exceptions are handled here
            # generally unless executor throws an OSError, the exception are caught and solved inplace
            processed_msg = self._callback(msg)
            # dont sent responses for CANCEL and IDLE control requests
            if msg.is_data_request or msg.request.command not in ['CANCEL', 'IDLE']:
                self._zmqstreamlet.send_message(processed_msg)
        except RuntimeTerminated:
            # this is the proper way to end when a terminate signal is sent
            self._zmqstreamlet.send_message(msg)
            self._zmqstreamlet.close()
        except KeyboardInterrupt as kbex:
            # save executor
            self.logger.debug(f'{kbex!r} causes the breaking from the event loop')
            self._zmqstreamlet.send_message(msg)
            self._zmqstreamlet.close(flush=False)
        except (SystemError, zmq.error.ZMQError) as ex:
            # save executor
            self.logger.debug(f'{ex!r} causes the breaking from the event loop')
            self._zmqstreamlet.send_message(msg)
            self._zmqstreamlet.close()
        except MemoryOverHighWatermark:
            self.logger.critical(
                f'memory usage {used_memory()} GB is above the high-watermark: {self.args.memory_hwm} GB'
            )
        except NoExplicitMessage:
            # silent and do not propagate message anymore
            # 1. wait partial message to be finished
            # 2. dealer send a control message and no need to go on
            pass
        except (RuntimeError, Exception, ChainedPodException) as ex:
            # general runtime error and nothing serious, we simply mark the message to error and pass on
            if not self.is_post_hook_done:
                self._post_hook(msg)

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

            self._zmqstreamlet.send_message(msg)

    #: Some class-specific properties

    @property
    def is_idle(self) -> bool:
        """
        Return ``True`` when current time is ``max_idle_time`` seconds late than the last active time

        :return: True if idle else false.
        """
        return (time.perf_counter() - self._last_active_time) > self.args.max_idle_time

    def _expect_parts(self, msg: 'Message') -> int:
        """
        The expected number of partial messages before trigger :meth:`handle`

        :param msg: The message from which to compute the expected parts
        :return: expected number of partial messages
        """
        if msg.is_data_request:
            if (
                self.args.socket_in == SocketType.ROUTER_BIND
                and not self._static_routing_table
            ):
                graph = RoutingTable(msg.envelope.routing_table)
                return graph.active_target_pod.expected_parts
            else:
                return self.args.num_part
        else:
            return 1

    # Static methods used by the Pea to communicate with the `Runtime` in the separate process

    @staticmethod
    def status(ctrl_address: str, timeout_ctrl: int):
        """
        Send get status control message.

        :param ctrl_address: the address where the control message needs to be sent
        :param timeout_ctrl: the timeout to wait for control messages to be processed

        :return: control message.
        """
        from ...zmq import send_ctrl_message

        return send_ctrl_message(
            ctrl_address, 'STATUS', timeout=timeout_ctrl, raise_exception=False
        )

    @staticmethod
    def is_ready(ctrl_address: str, timeout_ctrl: int) -> bool:
        """
        Check if status is ready.

        :param ctrl_address: the address where the control message needs to be sent
        :param timeout_ctrl: the timeout to wait for control messages to be processed

        :return: True if status is ready else False.
        """
        status = ZEDRuntime.status(ctrl_address, timeout_ctrl)
        return status and status.is_ready

    @staticmethod
    def wait_for_ready_or_shutdown(
        timeout: Optional[float],
        ctrl_address: str,
        timeout_ctrl: int,
        shutdown_event: Union['multiprocessing.Event', 'threading.Event'],
        **kwargs,
    ):
        """
        Check if the runtime has successfully started

        :param timeout: The time to wait before readiness or failure is determined
        :param ctrl_address: the address where the control message needs to be sent
        :param timeout_ctrl: the timeout to wait for control messages to be processed
        :param shutdown_event: the multiprocessing event to detect if the process failed
        :param kwargs: extra keyword arguments
        :return: True if is ready or it needs to be shutdown
        """
        timeout_ns = 1000000000 * timeout if timeout else None
        now = time.time_ns()
        while timeout_ns is None or time.time_ns() - now < timeout_ns:
            if shutdown_event.is_set() or ZEDRuntime.is_ready(
                ctrl_address, timeout_ctrl
            ):
                return True

        return False

    @staticmethod
    def _retry_control_message(
        ctrl_address: str,
        timeout_ctrl: int,
        command: str,
        num_retry: int,
        logger: 'JinaLogger',
    ):
        """Retry sending a control message with a given command for several trials
        :param ctrl_address: the address where the control message needs to be sent
        :param timeout_ctrl: the timeout to wait for control messages to be processed
        :param command: the command to send in the control message
        :param num_retry: the number of retries to successfully send the message
        :param logger: the JinaLogger to log messages
        """
        from ...zmq import send_ctrl_message

        for retry in range(1, num_retry + 1):
            logger.debug(f'Sending {command} command for the {retry}th time')
            try:
                send_ctrl_message(
                    ctrl_address,
                    command,
                    timeout=timeout_ctrl,
                    raise_exception=True,
                )
                break
            except Exception as ex:
                logger.warning(f'{ex!r}')
                if retry == num_retry:
                    raise ex

    @staticmethod
    def cancel(
        control_address: str,
        timeout_ctrl: int,
        socket_in_type: 'SocketType',
        skip_deactivate: bool,
        logger: 'JinaLogger',
        **kwargs,
    ):
        """
        Check if the runtime has successfully started

        :param control_address: the address where the control message needs to be sent
        :param timeout_ctrl: the timeout to wait for control messages to be processed
        :param socket_in_type: the type of input socket, needed to know if is a dealer
        :param skip_deactivate: flag to tell if deactivate signal may be missed.
            This is important when you want to independently kill a Runtime
        :param logger: the JinaLogger to log messages
        :param kwargs: extra keyword arguments
        """
        if not skip_deactivate and socket_in_type == SocketType.DEALER_CONNECT:
            ZEDRuntime._retry_control_message(
                ctrl_address=control_address,
                timeout_ctrl=timeout_ctrl,
                command='DEACTIVATE',
                num_retry=3,
                logger=logger,
            )
        ZEDRuntime._retry_control_message(
            ctrl_address=control_address,
            timeout_ctrl=timeout_ctrl,
            command='TERMINATE',
            num_retry=3,
            logger=logger,
        )

    @staticmethod
    def activate(
        control_address: str,
        timeout_ctrl: int,
        socket_in_type: 'SocketType',
        logger: 'JinaLogger',
        **kwargs,
    ):
        """
        Check if the runtime has successfully started

        :param control_address: the address where the control message needs to be sent
        :param timeout_ctrl: the timeout to wait for control messages to be processed
        :param socket_in_type: the type of input socket, needed to know if is a dealer
        :param logger: the JinaLogger to log messages
        :param kwargs: extra keyword arguments
        """
        if socket_in_type == SocketType.DEALER_CONNECT:
            ZEDRuntime._retry_control_message(
                ctrl_address=control_address,
                timeout_ctrl=timeout_ctrl,
                command='ACTIVATE',
                num_retry=3,
                logger=logger,
            )

    @staticmethod
    def get_control_address(host: str, port: str, **kwargs):
        """
        Get the control address for a runtime with a given host and port

        :param host: the host where the runtime works
        :param port: the control port where the runtime listens
        :param kwargs: extra keyword arguments
        :return: The corresponding control address
        """
        from ...zmq import Zmqlet

        return Zmqlet.get_ctrl_address(host, port, False)[0]
