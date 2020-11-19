__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
import multiprocessing
import os
import threading
import time
from collections import defaultdict
from multiprocessing.synchronize import Event
from typing import Dict, Optional, Union, List

import zmq

from jina.types.message import Message
from .zmq import send_ctrl_message, Zmqlet, ZmqStreamlet
from .. import __ready_msg__, __stop_msg__, Request
from ..enums import PeaRoleType, SkipOnErrorType
from ..excepts import NoExplicitMessage, ExecutorFailToLoad, MemoryOverHighWatermark, DriverError, PeaFailToStart, \
    ChainedPodException
from ..executors import BaseExecutor
from ..helper import is_valid_local_config_source, typename
from ..logging import JinaLogger
from ..logging.profile import used_memory, TimeDict
from ..proto import jina_pb2

__all__ = ['PeaMeta', 'BasePea']


class PeaMeta(type):
    """Meta class of :class:`BasePea` to enable switching between ``thread`` and ``process`` backend. """
    _dct = {}

    def __new__(cls, name, bases, dct):
        _cls = super().__new__(cls, name, bases, dct)
        PeaMeta._dct.update({name: {'cls': cls,
                                    'name': name,
                                    'bases': bases,
                                    'dct': dct}})
        return _cls

    def __call__(cls, *args, **kwargs) -> 'PeaMeta':
        # switch to the new backend
        _cls = {
            'thread': threading.Thread,
            'process': multiprocessing.Process,
        }.get(getattr(args[0], 'runtime', 'thread'))

        # rebuild the class according to mro
        for c in cls.mro()[-2::-1]:
            arg_cls = PeaMeta._dct[c.__name__]['cls']
            arg_name = PeaMeta._dct[c.__name__]['name']
            arg_dct = PeaMeta._dct[c.__name__]['dct']
            _cls = super().__new__(arg_cls, arg_name, (_cls,), arg_dct)

        return type.__call__(_cls, *args, **kwargs)


def _get_event(obj: 'BasePea') -> Event:
    if isinstance(obj, threading.Thread):
        return threading.Event()
    elif isinstance(obj, multiprocessing.Process):
        return multiprocessing.Event()
    else:
        raise NotImplementedError


def _make_or_event(obj: 'BasePea', *events) -> Event:
    or_event = _get_event(obj)

    def or_set(self):
        self._set()
        self.changed()

    def or_clear(self):
        self._clear()
        self.changed()

    def orify(e, changed_callback):
        e._set = e.set
        e._clear = e.clear
        e.changed = changed_callback
        e.set = lambda: or_set(e)
        e.clear = lambda: or_clear(e)

    def changed():
        bools = [e.is_set() for e in events]
        if any(bools):
            or_event.set()
        else:
            or_event.clear()

    for e in events:
        orify(e, changed)
    changed()
    return or_event


class BasePea(metaclass=PeaMeta):
    """BasePea is an unary service unit which provides network interface and
    communicates with others via protobuf and ZeroMQ
    """

    def __init__(self, args: Union['argparse.Namespace', Dict]):
        """ Create a new :class:`BasePea` object

        :param args: the arguments received from the CLI
        :param pea_id: the id used to separate the storage of each pea, only used when ``args.separate_storage=True``
        """
        super().__init__()
        self.args = args
        self.name = self.__class__.__name__  #: this is the process name

        self.is_ready_event = _get_event(self)
        self.is_shutdown = _get_event(self)
        self.ready_or_shutdown = _make_or_event(self, self.is_ready_event, self.is_shutdown)
        self.is_shutdown.clear()

        self.last_active_time = time.perf_counter()
        self.last_dump_time = time.perf_counter()

        self._timer = TimeDict()

        self._request = None
        self._message = None

        # all pending messages collected so far, key is the request id
        self._pending_msgs = defaultdict(list)  # type: Dict[str, List['Message']]
        self._partial_requests = None
        self._partial_messages = None

        if isinstance(self.args, argparse.Namespace):
            self.daemon = args.daemon
            if self.args.name:
                self.name = self.args.name
            if self.args.role == PeaRoleType.PARALLEL:
                self.name = f'{self.name}-{self.args.pea_id}'
            self.ctrl_addr, self.ctrl_with_ipc = Zmqlet.get_ctrl_address(self.args)
            self.logger = JinaLogger(self.name,
                                     log_id=self.args.log_id,
                                     log_config=self.args.log_config)
        else:
            self.logger = JinaLogger(self.name)

    def __str__(self):
        r = self.name
        if getattr(self, 'executor', None):
            r += f'({str(self.executor)})'
        return r

    def handle(self, msg: 'Message') -> 'BasePea':
        """Register the current message to this pea, so that all message-related properties are up-to-date, including
        :attr:`request`, :attr:`prev_requests`, :attr:`message`, :attr:`prev_messages`. And then call the executor to handle
        this message if its envelope's  status is not ERROR, else skip handling of message.

        :param msg: the message received
        """

        if self.expect_parts > 1 and self.expect_parts > len(self.partial_requests):
            # NOTE: reduce priority is higher than chain exception
            # otherwise a reducer will lose its function when eailier pods raise exception
            raise NoExplicitMessage

        if msg.envelope.status.code != jina_pb2.StatusProto.ERROR or self.args.skip_on_error < SkipOnErrorType.HANDLE:
            self.executor(self.request_type)
        else:
            raise ChainedPodException
        return self

    @property
    def is_idle(self) -> bool:
        """Return ``True`` when current time is ``max_idle_time`` seconds late than the last active time"""
        return (time.perf_counter() - self.last_active_time) > self.args.max_idle_time

    @property
    def request(self) -> 'Request':
        """Get the current request body inside the protobuf message"""
        return self._request

    @property
    def message(self) -> 'Message':
        """Get the current protobuf message to be processed"""
        return self._message

    @property
    def request_type(self) -> str:
        return self._message.envelope.request_type

    def load_executor(self):
        """Load the executor to this BasePea, specified by ``uses`` CLI argument.

        """
        try:
            self.executor = BaseExecutor.load_config(
                self.args.uses if is_valid_local_config_source(self.args.uses) else self.args.uses_internal,
                self.args.separated_workspace, self.args.pea_id)
            self.executor.attach(pea=self)
        except FileNotFoundError as ex:
            self.logger.error(f'fail to load file dependency: {repr(ex)}')
            raise ExecutorFailToLoad from ex
        except Exception as ex:
            raise ExecutorFailToLoad from ex

    def print_stats(self):
        self.logger.info(
            ' '.join(f'{k}: {v / self._timer.accum_time["loop"]:.2f}' for k, v in self._timer.accum_time.items()))

    def save_executor(self, dump_interval: int = 0):
        """Save the contained executor

        :param dump_interval: the time interval for saving
        """
        if ((time.perf_counter() - self.last_dump_time) > self.args.dump_interval > 0) or dump_interval <= 0:
            if self.args.read_only:
                self.logger.debug('executor is not saved as "read_only" is set to true for this BasePea')
            elif not hasattr(self, 'executor'):
                self.logger.debug('this BasePea contains no executor, no need to save')
            elif self.executor.save():
                self.logger.info('dumped changes to the executor, %3.0fs since last the save'
                                 % (time.perf_counter() - self.last_dump_time))
            else:
                self.logger.info('executor says there is nothing to save')
            self.last_dump_time = time.perf_counter()
            if hasattr(self, 'zmqlet'):
                self.zmqlet.print_stats()

    @property
    def expect_parts(self) -> int:
        """The expected number of partial messages before trigger :meth:`handle` """
        return self.args.num_part if self.message.is_data_request else 1

    @property
    def partial_requests(self) -> List['Request']:
        """The collected partial requests under the current ``request_id`` """
        return self._partial_requests

    @property
    def partial_messages(self) -> List['Message']:
        """The collected partial messages under the current ``request_id`` """
        return self._partial_messages

    def pre_hook(self, msg: 'Message') -> 'BasePea':
        """Pre-hook function, what to do after first receiving the message """
        msg.add_route(self.name, self.args.identity)
        self._request = msg.request
        self._message = msg

        part_str = ' '
        if self.expect_parts > 1:
            req_id = msg.envelope.request_id
            self._pending_msgs[req_id].append(msg)
            self._partial_messages = self._pending_msgs[req_id]
            self._partial_requests = [v.request for v in self._partial_messages]
            part_str = f' ({len(self.partial_requests)}/{self.expect_parts} parts) '

        self.logger.info(f'recv {msg.envelope.request_type}{part_str}from {msg.colored_route}')
        return self

    def post_hook(self, msg: 'Message') -> 'BasePea':
        """Post-hook function, what to do before handing out the message """
        # self.logger.critical(f'is message used: {msg.request.is_used}')
        self.last_active_time = time.perf_counter()
        self.save_executor(self.args.dump_interval)
        self.check_memory_watermark()

        if self.expect_parts > 1:
            msgs = self._pending_msgs.pop(msg.envelope.request_id)
            msg.merge_envelope_from(msgs)

        msg.update_timestamp()
        return self

    def set_ready(self, *args, **kwargs):
        """Set the status of the pea to ready """
        self.is_ready_event.set()
        self.logger.success(__ready_msg__)

    def unset_ready(self, *args, **kwargs):
        """Set the status of the pea to shutdown """
        self.is_ready_event.clear()
        self.logger.success(__stop_msg__)

    def _callback(self, msg: 'Message'):
        self.is_post_hook_done = False  #: if the post_hook is called
        self.pre_hook(msg).handle(msg).post_hook(msg)
        self.is_post_hook_done = True
        return msg

    def _handle_terminate_signal(self, msg):
        # save executor
        if hasattr(self, 'executor'):
            if not self.args.exit_no_dump:
                self.save_executor(dump_interval=0)
            self.executor.close()

        # serious error happen in callback, we need to break the event loop
        self.zmqlet.send_message(msg)
        # note, the logger can only be put on the second last line before `close`, as when
        # `close` is called, the callback is unregistered and everything after `close` can not be reached
        # some black magic in eventloop i guess?
        self.loop_teardown()
        self.is_shutdown.set()

    def msg_callback(self, msg: 'Message') -> Optional['Message']:
        """Callback function after receiving the message

        When nothing is returned then the nothing is send out via :attr:`zmqlet.sock_out`.
        """
        try:
            # notice how executor related exceptions are handled here
            # generally unless executor throws an OSError, the exception are caught and solved inplace
            self.zmqlet.send_message(self._callback(msg))
        except (SystemError, zmq.error.ZMQError, KeyboardInterrupt) as ex:
            # save executor
            self.logger.info(f'{repr(ex)} causes the breaking from the event loop')
            self._handle_terminate_signal(msg)
        except MemoryOverHighWatermark:
            self.logger.critical(
                f'memory usage {used_memory()} GB is above the high-watermark: {self.args.memory_hwm} GB')
        except NoExplicitMessage:
            # silent and do not propagate message anymore
            # 1. wait partial message to be finished
            # 2. dealer send a control message and no need to go on
            pass
        except (RuntimeError, Exception, ChainedPodException) as ex:
            # general runtime error and nothing serious, we simply mark the message to error and pass on
            if not self.is_post_hook_done:
                self.post_hook(msg)
            if isinstance(ex, ChainedPodException):
                msg.add_exception()
                self.logger.warning(repr(ex))
            else:
                msg.add_exception(ex, executor=getattr(self, 'executor'))
                self.logger.error(repr(ex))
            if 'JINA_RAISE_ERROR_EARLY' in os.environ:
                raise
            self.zmqlet.send_message(msg)

    def loop_body(self):
        """The body of the request loop

        .. note::

            Class inherited from :class:`BasePea` must override this function. And add
            :meth:`set_ready` when your loop body is started
        """
        os.environ['JINA_POD_NAME'] = self.name
        os.environ['JINA_LOG_ID'] = self.args.log_id
        self.load_plugins()
        self.load_executor()
        self.zmqlet = ZmqStreamlet(self.args, logger=self.logger)
        self.set_ready()
        self.zmqlet.start(self.msg_callback)

    def load_plugins(self):
        if self.args.py_modules:
            from ..importer import PathImporter
            PathImporter.add_modules(*self.args.py_modules)

    def loop_teardown(self):
        """Stop the request loop """
        if hasattr(self, 'zmqlet'):
            self.zmqlet.close()

    def run(self):
        """Start the request loop of this BasePea. It will listen to the network protobuf message via ZeroMQ. """
        try:
            # Every logger created in this process will be identified by the `Pod Id` and use the same name
            self.post_init()
            self.loop_body()
        except ExecutorFailToLoad:
            self.logger.critical(f'can not start a executor from {self.args.uses}', exc_info=True)
        except KeyboardInterrupt:
            self.logger.info('Loop interrupted by user')
        except SystemError as ex:
            self.logger.error(f'SystemError interrupted pea loop {repr(ex)}')
        except DriverError as ex:
            self.logger.critical(f'driver error: {repr(ex)}', exc_info=True)
        except zmq.error.ZMQError:
            self.logger.critical('zmqlet can not be initiated')
        except Exception as ex:
            # this captures the general exception from the following places:
            # - self.zmqlet.recv_message
            # - self.zmqlet.send_message
            self.logger.critical(f'unknown exception: {repr(ex)}', exc_info=True)
        finally:
            # if an exception occurs this unsets ready and shutting down
            self.loop_teardown()
            self.unset_ready()
            self.is_shutdown.set()

    def check_memory_watermark(self):
        """Check the memory watermark """
        if used_memory() > self.args.memory_hwm > 0:
            raise MemoryOverHighWatermark

    def post_init(self):
        """Post initializer after the start of the request loop via :func:`run`, so that they can be kept in the same
        process/thread as the request loop.

        """
        pass

    def send_terminate_signal(self) -> None:
        """Gracefully close this pea and release all resources """
        if self.is_ready_event.is_set() and hasattr(self, 'ctrl_addr'):
            send_ctrl_message(self.ctrl_addr, jina_pb2.RequestProto.ControlRequestProto.TERMINATE,
                              timeout=self.args.timeout_ctrl)

    @property
    def status(self):
        """Send the control signal ``STATUS`` to itself and return the status """
        if self.is_ready_event.is_set() and getattr(self, 'ctrl_addr'):
            return send_ctrl_message(self.ctrl_addr, jina_pb2.RequestProto.ControlRequestProto.STATUS,
                                     timeout=self.args.timeout_ctrl)

    def start(self) -> 'BasePea':
        super().start()
        if isinstance(self.args, dict):
            _timeout = getattr(self.args['peas'][0], 'timeout_ready', -1)
        else:
            _timeout = getattr(self.args, 'timeout_ready', -1)

        if _timeout <= 0:
            _timeout = None
        else:
            _timeout /= 1e3

        if self.ready_or_shutdown.wait(_timeout):
            if self.is_shutdown.is_set():
                # return too early and the shutdown is set, means something fails!!
                self.logger.critical(f'fail to start {typename(self)} with name {self.name}, '
                                     f'this often means the executor used in the pod is not valid')
                raise PeaFailToStart
            return self
        else:
            raise TimeoutError(
                f'{typename(self)} with name {self.name} can not be initialized after {_timeout * 1e3}ms')

    def __enter__(self) -> 'BasePea':
        return self.start()

    def close(self) -> None:
        self.send_terminate_signal()
        self.is_shutdown.wait()
        if not self.daemon:
            self.logger.close()
            self.join()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
