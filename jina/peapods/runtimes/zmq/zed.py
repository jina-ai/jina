import argparse
import re
import time
from collections import defaultdict
from typing import Dict, List

import zmq

from .base import ZMQRuntime
from ...zmq import ZmqStreamlet
from .... import __default_endpoint__
from ....enums import OnErrorStrategy, SocketType
from ....excepts import (
    NoExplicitMessage,
    ExecutorFailToLoad,
    MemoryOverHighWatermark,
    ChainedPodException,
    BadConfigSource,
    RuntimeTerminated,
    UnknownControlCommand,
)
from ....executors import BaseExecutor
from ....helper import random_identity, typename
from ....logging.profile import used_memory
from ....proto import jina_pb2
from ....types.arrays.document import DocumentArray
from ....types.message import Message
from ....types.request import Request
from ....types.routing.table import RoutingTable


class ZEDRuntime(ZMQRuntime):
    """Runtime procedure leveraging :class:`ZmqStreamlet` for Executor."""

    def __init__(self, args: 'argparse.Namespace', ctrl_addr: str, **kwargs):
        """Initialize private parameters and execute private loading functions.

        :param args: args from CLI
        :param ctrl_addr: control port address
        :param kwargs: extra keyword arguments
        """
        super().__init__(args, ctrl_addr, **kwargs)
        self._id = random_identity()
        self._last_active_time = time.perf_counter()

        self._request = None
        self._message = None

        # all pending messages collected so far, key is the request id
        self._pending_msgs = defaultdict(list)  # type: Dict[str, List['Message']]
        self._partial_requests = None
        self._partial_messages = None

        # idle_dealer_ids only becomes non-None when it receives IDLE ControlRequest
        self._idle_dealer_ids = set()

        self._load_zmqstreamlet()
        self._load_plugins()
        self._load_executor()

    def run_forever(self):
        """Start the `ZmqStreamlet`."""
        self._zmqstreamlet.start(self._msg_callback)

    def teardown(self):
        """Close the `ZmqStreamlet` and `Executor`."""
        self._zmqstreamlet.close()
        self._executor.close()
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
            ready_event=self.is_ready_event,
        )

    def _load_executor(self):
        """Load the executor to this runtime, specified by ``uses`` CLI argument."""
        try:
            self._executor = BaseExecutor.load_config(
                self.args.uses,
                override_with=self.args.override_with,
                override_metas=self.args.override_metas,
                runtime_args=vars(self.args),
            )
        except BadConfigSource as ex:
            self.logger.error(
                f'fail to load config from {self.args.uses}, if you are using docker image for --uses, '
                f'please use "docker://YOUR_IMAGE_NAME"'
            )
            raise ExecutorFailToLoad from ex
        except FileNotFoundError as ex:
            self.logger.error(f'fail to load file dependency')
            raise ExecutorFailToLoad from ex
        except Exception as ex:
            self.logger.critical(f'can not load the executor from {self.args.uses}')
            raise ExecutorFailToLoad from ex

    def _load_plugins(self):
        """Load the plugins if needed necessary to load executors."""
        if self.args.py_modules:
            from ....importer import PathImporter

            PathImporter.add_modules(*self.args.py_modules)

    #: Private methods required by :meth:`teardown`
    def _check_memory_watermark(self):
        """Check the memory watermark."""
        if used_memory() > self.args.memory_hwm > 0:
            raise MemoryOverHighWatermark

    #: Private methods required by run_forever
    def _pre_hook(self, msg: 'Message') -> 'ZEDRuntime':
        """
        Pre-hook function, what to do after first receiving the message.

        :param msg: received message
        :return: `ZEDRuntime`
        """
        msg.add_route(self.name, self._id)
        self._request = msg.request
        self._message = msg

        if self.expect_parts > 1:
            req_id = msg.envelope.request_id
            self._pending_msgs[req_id].append(msg)
            self._partial_messages = self._pending_msgs[req_id]
            self._partial_requests = [v.request for v in self._partial_messages]

        if self.logger.debug_enabled:
            self._log_info_msg(
                msg,
                f'({len(self.partial_requests)}/{self.expect_parts} parts)'
                if self.expect_parts > 1
                else '',
            )

        if self.expect_parts > 1 and self.expect_parts > len(self.partial_requests):
            # NOTE: reduce priority is higher than chain exception
            # otherwise a reducer will lose its function when earlier pods raise exception
            raise NoExplicitMessage

        if self.request_type == 'ControlRequest':
            self._handle_control_req()

        if (
            msg.envelope.status.code == jina_pb2.StatusProto.ERROR
            and self.args.on_error_strategy >= OnErrorStrategy.SKIP_HANDLE
        ):
            raise ChainedPodException

        return self

    def _log_info_msg(self, msg, part_str):
        info_msg = f'recv {msg.envelope.request_type} '
        if self.request_type == 'DataRequest':
            info_msg += f'({self.envelope.header.exec_endpoint}) - ({self.envelope.request_id}) '
        elif self.request_type == 'ControlRequest':
            info_msg += f'({self.request.command}) '
        info_msg += f'{part_str} from {msg.colored_route}'
        self.logger.debug(info_msg)

    def _post_hook(self, msg: 'Message') -> 'ZEDRuntime':
        """
        Post-hook function, what to do before handing out the message.

        :param msg: received message
        :return: `ZEDRuntime`
        """
        # do NOT access `msg.request.*` in the _pre_hook, as it will trigger the deserialization
        # all meta information should be stored and accessed via `msg.envelope`

        self._last_active_time = time.perf_counter()
        self._check_memory_watermark()

        if self.expect_parts > 1:
            msgs = self._pending_msgs.pop(msg.envelope.request_id)
            msg.merge_envelope_from(msgs)

        msg.update_timestamp()
        return self

    @staticmethod
    def _parse_params(parameters: Dict, executor_name: str):
        parsed_params = parameters
        specific_parameters = parameters.get(executor_name, None)
        if specific_parameters:
            parsed_params.update(**specific_parameters)
        return parsed_params

    def _handle(self) -> 'ZEDRuntime':
        """Register the current message to this pea, so that all message-related properties are up-to-date, including
        :attr:`request`, :attr:`prev_requests`, :attr:`message`, :attr:`prev_messages`. And then call the executor to handle
        this message if its envelope's  status is not ERROR, else skip handling of message.

        .. note::
            Handle does not handle explicitly message because it may wait for different messages when different parts are expected
        :return: ZEDRuntime procedure.
        """
        # skip executor for non-DataRequest
        if self.request_type != 'DataRequest':
            self.logger.debug(f'skip executor: not data request')
            return self

        # migrated from the previously RouteDriver logic
        # set dealer id
        if self._idle_dealer_ids:
            dealer_id = self._idle_dealer_ids.pop()
            self.envelope.receiver_id = dealer_id

            # when no available dealer, pause the pollin from upstream
            if not self._idle_dealer_ids:
                self._zmqstreamlet.pause_pollin()
            self.logger.debug(
                f'using route, set receiver_id: {self.envelope.receiver_id}'
            )

        # skip executor if target_peapod mismatch
        if not re.match(self.envelope.header.target_peapod, self.name):
            self.logger.debug(
                f'skip executor: mismatch target, target: {self.envelope.header.target_peapod}, name: {self.name}'
            )
            return self

        # skip executor if endpoints mismatch
        if (
            self.envelope.header.exec_endpoint not in self._executor.requests
            and __default_endpoint__ not in self._executor.requests
        ):
            self.logger.debug(
                f'skip executor: mismatch request, exec_endpoint: {self.envelope.header.exec_endpoint}, requests: {self._executor.requests}'
            )
            return self

        params = self._parse_params(self.request.parameters, self._executor.metas.name)

        # executor logic
        r_docs = self._executor(
            req_endpoint=self.envelope.header.exec_endpoint,
            docs=self.docs,
            parameters=params,
            docs_matrix=self.docs_matrix,
            groundtruths=self.groundtruths,
            groundtruths_matrix=self.groundtruths_matrix,
        )

        # assigning result back to request
        # 1. Return none: do nothing
        # 2. Return nonempty and non-DocumentArray: raise error
        # 3. Return DocArray, but the memory pointer says it is the same as self.docs: do nothing
        # 4. Return DocArray and its not a shallow copy of self.docs: assign self.request.docs
        if r_docs is not None:
            if not isinstance(r_docs, DocumentArray):
                raise TypeError(
                    f'return type must be {DocumentArray!r} or None, but getting {typename(r_docs)}'
                )
            elif r_docs != self.request.docs:
                # this means the returned DocArray is a completely new one
                self.request.docs.clear()
                self.request.docs.extend(r_docs)

        return self

    def _handle_control_req(self):
        # migrated from previous ControlDriver logic
        if self.request.command == 'TERMINATE':
            self.envelope.status.code = jina_pb2.StatusProto.SUCCESS
            raise RuntimeTerminated
        elif self.request.command == 'STATUS':
            self.envelope.status.code = jina_pb2.StatusProto.READY
            self.request.parameters = vars(self.args)
        elif self.request.command == 'IDLE':
            self._idle_dealer_ids.add(self.envelope.receiver_id)
            self._zmqstreamlet.resume_pollin()
            self.logger.debug(
                f'{self.envelope.receiver_id} is idle, now I know these idle peas {self._idle_dealer_ids}'
            )
        elif self.request.command == 'CANCEL':
            if self.envelope.receiver_id in self._idle_dealer_ids:
                self._idle_dealer_ids.remove(self.envelope.receiver_id)
        elif self.request.command == 'ACTIVATE':
            self._zmqstreamlet._send_idle_to_router()
        elif self.request.command == 'DEACTIVATE':
            self._zmqstreamlet._send_cancel_to_router()
        else:
            raise UnknownControlCommand(
                f'don\'t know how to handle {self.request.command}'
            )

    def _callback(self, msg: 'Message'):
        self.is_post_hook_done = False  #: if the post_hook is called
        self._pre_hook(msg)._handle()._post_hook(msg)
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
                msg.add_exception(ex, executor=getattr(self, '_executor'))
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

    @property
    def request(self) -> 'Request':
        """
        Get the current request body inside the protobuf message

        :return: :class:`ZEDRuntime` request
        """
        return self._request

    @property
    def message(self) -> 'Message':
        """
        Get the current protobuf message to be processed

        :return: :class:`ZEDRuntime` message
        """
        return self._message

    @property
    def request_type(self) -> str:
        """
        Get the type of message being processed

        :return: request type
        """
        return self._message.envelope.request_type

    @property
    def expect_parts(self) -> int:
        """
        The expected number of partial messages before trigger :meth:`handle`

        :return: expected number of partial messages
        """
        if self.message.is_data_request:
            if self.args.socket_in == SocketType.ROUTER_BIND:
                graph = RoutingTable(self._message.envelope.routing_table)
                return graph.active_target_pod.expected_parts
            else:
                return self.args.num_part
        else:
            return 1

    @property
    def partial_requests(self) -> List['Request']:
        """
        The collected partial requests under the current ``request_id``

        :return: collected partial requests
        """
        return self._partial_requests

    @property
    def partial_messages(self) -> List['Message']:
        """
        The collected partial messages under the current ``request_id`` "
        :return: collected partial messages

        """
        return self._partial_messages

    def _get_docs(self, field: str) -> 'DocumentArray':
        if self.expect_parts > 1:
            result = DocumentArray(
                [d for r in reversed(self.partial_requests) for d in getattr(r, field)]
            )
        else:
            result = getattr(self.request, field)

        # to unify all length=0 DocumentArray (or any other results) will simply considered as None
        # otherwise the executor has to handle DocArray(0)
        if len(result):
            return result

    def _get_docs_matrix(self, field) -> List['DocumentArray']:
        """DocumentArray from (multiple) requests

        :param field: either `docs` or `groundtruths`

        .. # noqa: DAR201"""
        if self.expect_parts > 1:
            result = [getattr(r, field) for r in reversed(self.partial_requests)]
        else:
            result = [getattr(self.request, field)]

        # to unify all length=0 DocumentArray (or any other results) will simply considered as None
        # otherwise, the executor has to handle [None, None, None] or [DocArray(0), DocArray(0), DocArray(0)]
        len_r = sum(len(r) for r in result)
        if len_r:
            return result

    @property
    def docs(self) -> 'DocumentArray':
        """Return a DocumentArray by concatenate (multiple) ``requests.docs``

        .. # noqa: DAR201"""
        return self._get_docs('docs')

    @property
    def groundtruths(self) -> 'DocumentArray':
        """Return a DocumentArray by concatenate (multiple) ``requests.groundtruths``

        .. # noqa: DAR201"""
        return self._get_docs('groundtruths')

    @property
    def docs_matrix(self) -> List['DocumentArray']:
        """Return a list of DocumentArray from multiple requests

        .. # noqa: DAR201"""
        return self._get_docs_matrix('docs')

    @property
    def groundtruths_matrix(self) -> List['DocumentArray']:
        """A flattened DocumentArray from (multiple) requests

        .. # noqa: DAR201"""
        return self._get_docs_matrix('groundtruths')

    @property
    def envelope(self) -> 'jina_pb2.EnvelopeProto':
        """Get the current message envelope

        .. # noqa: DAR201
        """
        return self._message.envelope
