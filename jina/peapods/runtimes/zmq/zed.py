import time
from collections import defaultdict
from typing import Dict, List

import zmq

from .base import ZMQRuntime
from ...zmq import ZmqStreamlet
from .... import Message
from .... import Request
from ....enums import OnErrorStrategy
from ....excepts import (
    NoExplicitMessage,
    ExecutorFailToLoad,
    MemoryOverHighWatermark,
    ChainedPodException,
    BadConfigSource,
    RuntimeTerminated,
)
from ....executors import BaseExecutor
from ....helper import random_identity
from ....logging.profile import used_memory, TimeDict
from ....proto import jina_pb2


class ZEDRuntime(ZMQRuntime):
    """Runtime procedure leveraging :class:`ZmqStreamlet` for Executor, Driver."""

    def run_forever(self):
        """Start the `ZmqStreamlet`."""
        self._zmqlet.start(self._msg_callback)

    def setup(self):
        """Initialize private parameters and execute private loading functions."""
        self._id = random_identity()
        self._last_active_time = time.perf_counter()
        self._last_dump_time = time.perf_counter()
        self._last_load_time = time.perf_counter()

        self._timer = TimeDict()

        self._request = None
        self._message = None

        # all pending messages collected so far, key is the request id
        self._pending_msgs = defaultdict(list)  # type: Dict[str, List['Message']]
        self._partial_requests = None
        self._partial_messages = None

        self._load_zmqlet()
        self._load_plugins()
        self._load_executor()

    def teardown(self):
        """Close the `ZmqStreamlet` and `Executor`."""
        self._zmqlet.close()
        self._executor.close()
        super().teardown()

    #: Private methods required by :meth:`setup`

    def _load_zmqlet(self):
        """Load ZMQStreamlet to this runtime."""
        # important: fix zmqstreamlet ctrl address to replace the the ctrl address generated in the main
        # process/thread
        self._zmqlet = ZmqStreamlet(
            self.args, logger=self.logger, ctrl_addr=self.ctrl_addr
        )

    def _load_executor(self):
        """Load the executor to this runtime, specified by ``uses`` CLI argument."""
        try:
            self._executor = BaseExecutor.load_config(
                self.args.uses, pea_id=self.args.pea_id, read_only=self.args.read_only
            )
            self._executor.attach(runtime=self)
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

    def _save_executor(self):
        """Save the contained executor according to the `dump_interval` parameter."""
        if (time.perf_counter() - self._last_dump_time) > self.args.dump_interval > 0:
            self._executor.save()
            self._last_dump_time = time.perf_counter()

    def _reload_executor(self):
        if (time.perf_counter() - self._last_load_time) > self.args.load_interval > 0:
            self._load_executor()
            self._last_load_time = time.perf_counter()

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
        self._reload_executor()
        self._request = msg.request
        self._message = msg

        part_str = ''
        if self.expect_parts > 1:
            req_id = msg.envelope.request_id
            self._pending_msgs[req_id].append(msg)
            self._partial_messages = self._pending_msgs[req_id]
            self._partial_requests = [v.request for v in self._partial_messages]
            part_str = f'({len(self.partial_requests)}/{self.expect_parts} parts)'

        self.logger.info(
            f'recv {msg.envelope.request_type} {part_str} from {msg.colored_route}'
        )
        return self

    def _post_hook(self, msg: 'Message') -> 'ZEDRuntime':
        """
        Post-hook function, what to do before handing out the message.

        :param msg: received message
        :return: `ZEDRuntime`
        """
        self._last_active_time = time.perf_counter()
        self._save_executor()
        self._zmqlet.print_stats()
        self._check_memory_watermark()

        if self.expect_parts > 1:
            msgs = self._pending_msgs.pop(msg.envelope.request_id)
            msg.merge_envelope_from(msgs)

        msg.update_timestamp()
        return self

    def _handle(self, msg: 'Message') -> 'ZEDRuntime':
        """Register the current message to this pea, so that all message-related properties are up-to-date, including
        :attr:`request`, :attr:`prev_requests`, :attr:`message`, :attr:`prev_messages`. And then call the executor to handle
        this message if its envelope's  status is not ERROR, else skip handling of message.

        :param msg: the message received
        :return: ZEDRuntime procedure.
        """
        if self.expect_parts > 1 and self.expect_parts > len(self.partial_requests):
            # NOTE: reduce priority is higher than chain exception
            # otherwise a reducer will lose its function when eailier pods raise exception
            raise NoExplicitMessage

        if (
            msg.envelope.status.code != jina_pb2.StatusProto.ERROR
            or self.args.on_error_strategy < OnErrorStrategy.SKIP_HANDLE
        ):
            self._executor(self.request_type)
        else:
            raise ChainedPodException
        return self

    def _callback(self, msg: 'Message'):
        self.is_post_hook_done = False  #: if the post_hook is called
        self._pre_hook(msg)._handle(msg)._post_hook(msg)
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
            self._zmqlet.send_message(self._callback(msg))
        except RuntimeTerminated:
            # this is the proper way to end when a terminate signal is sent
            self._zmqlet.send_message(msg)
            self._zmqlet.close()
        except (SystemError, zmq.error.ZMQError, KeyboardInterrupt) as ex:
            # save executor
            self.logger.info(f'{ex!r} causes the breaking from the event loop')
            self._zmqlet.send_message(msg)
            self._zmqlet.close()
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
                msg.add_exception()
                self.logger.error(
                    f'{ex!r}'
                    + f'\n add "--quiet-error" to suppress the exception details'
                    if not self.args.quiet_error
                    else '',
                    exc_info=not self.args.quiet_error,
                )
            else:
                msg.add_exception(ex, executor=getattr(self, '_executor'))
                self.logger.error(
                    f'{ex!r}'
                    + f'\n add "--quiet-error" to suppress the exception details'
                    if not self.args.quiet_error
                    else '',
                    exc_info=not self.args.quiet_error,
                )

            self._zmqlet.send_message(msg)

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
        return self.args.num_part if self.message.is_data_request else 1

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
