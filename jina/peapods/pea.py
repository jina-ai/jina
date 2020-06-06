__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
import multiprocessing
import os
import threading
import time
from queue import Empty
from typing import Dict, Optional, Union

import zmq

from .zmq import send_ctrl_message, Zmqlet
from .. import __ready_msg__, __stop_msg__
from ..drivers.helper import routes2str, add_route
from ..enums import PeaRoleType
from ..excepts import NoExplicitMessage, ExecutorFailToLoad, MemoryOverHighWatermark, UnknownControlCommand, \
    RequestLoopEnd, \
    DriverNotInstalled, NoDriverForRequest
from ..executors import BaseExecutor
from ..logging import get_logger
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

    def __call__(cls, *args, **kwargs):
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


def _get_event(obj):
    if isinstance(obj, threading.Thread):
        return threading.Event()
    elif isinstance(obj, multiprocessing.Process):
        return multiprocessing.Event()
    else:
        raise NotImplementedError


def _make_or_event(obj, *events):
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
        :param replica_id: the id used to separate the storage of each pea, only used when ``args.separate_storage=True``
        """
        super().__init__()
        self.args = args
        self.name = self.__class__.__name__  #: this is the process name
        self.daemon = True

        self.is_ready = _get_event(self)
        self.is_shutdown = _get_event(self)
        self.ready_or_shutdown = _make_or_event(self, self.is_ready, self.is_shutdown)
        self.is_shutdown.clear()

        # self.is_busy = _get_event(self)
        # # label the pea as busy until the loop body start
        # self.is_busy.set()

        self.last_active_time = time.perf_counter()
        self.last_dump_time = time.perf_counter()

        self._timer = TimeDict()

        self._request = None
        self._message = None

        if isinstance(args, argparse.Namespace):
            if args.name:
                self.name = args.name
            if args.role == PeaRoleType.HEAD:
                self.name = '%s-head' % self.name
            elif args.role == PeaRoleType.TAIL:
                self.name = '%s-tail' % self.name
            elif args.role == PeaRoleType.REPLICA:
                self.name = '%s-%d' % (self.name, args.replica_id)
            self.ctrl_addr, self.ctrl_with_ipc = Zmqlet.get_ctrl_address(args)
            if not args.log_with_own_name and args.name:
                # everything in this Pea (process) will use the same name for display the log
                os.environ['JINA_POD_NAME'] = args.name
            self.logger = get_logger(self.name, **vars(args))
        else:
            self.logger = get_logger(self.name)

    def handle(self, msg: 'jina_pb2.Message') -> 'BasePea':
        """Register the current message to this pea, so that all message-related properties are up-to-date, including
        :attr:`request`, :attr:`prev_requests`, :attr:`message`, :attr:`prev_messages`. And then call the executor to handle
        this message.

        :param msg: the message received
        """
        self.executor(self.request_type)
        return self

    @property
    def is_idle(self) -> bool:
        """Return ``True`` when current time is ``max_idle_time`` seconds late than the last active time"""
        return (time.perf_counter() - self.last_active_time) > self.args.max_idle_time

    @property
    def request(self) -> 'jina_pb2.Request':
        """Get the current request body inside the protobuf message"""
        return self._request

    @property
    def message(self) -> 'jina_pb2.Message':
        """Get the current protobuf message to be processed"""
        return self._message

    @property
    def request_type(self) -> str:
        return self._request.__class__.__name__

    @property
    def log_iterator(self):
        """Get the last log using iterator """
        from ..logging.queue import __log_queue__
        while self.is_ready.is_set():
            try:
                yield __log_queue__.get_nowait()
            except Empty:
                pass

    def load_executor(self):
        """Load the executor to this BasePea, specified by ``exec_yaml_path`` CLI argument.

        """
        if self.args.yaml_path:
            try:
                self.executor = BaseExecutor.load_config(self.args.yaml_path,
                                                         self.args.separated_workspace, self.args.replica_id)
                self.executor.attach(pea=self)
                # self.logger = get_logger('%s(%s)' % (self.name, self.executor.name), **vars(self.args))
            except FileNotFoundError:
                raise ExecutorFailToLoad
        else:
            self.logger.warning('this BasePea has no executor attached, you may want to double-check '
                                'if it is a mistake or on purpose (using this BasePea as router/map-reduce)')

    def print_stats(self):
        self.logger.info(
            ' '.join('%s: %.2f' % (k, v / self._timer.accum_time['loop']) for k, v in self._timer.accum_time.items()))

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

    def pre_hook(self, msg: 'jina_pb2.Message') -> 'BasePea':
        """Pre-hook function, what to do after first receiving the message """
        msg_type = msg.request.WhichOneof('body')
        self.logger.info('received "%s" from %s' % (msg_type, routes2str(msg, flag_current=True)))
        add_route(msg.envelope, self.name, self.args.identity)
        self._request = getattr(msg.request, msg_type)
        self._message = msg
        return self

    def post_hook(self, msg: 'jina_pb2.Message') -> 'BasePea':
        """Post-hook function, what to do before handing out the message """
        msg.envelope.routes[-1].end_time.GetCurrentTime()
        return self

    def set_ready(self, *args, **kwargs):
        """Set the status of the pea to ready """
        self.is_ready.set()
        self.logger.success(__ready_msg__)

    def unset_ready(self, *args, **kwargs):
        """Set the status of the pea to shutdown """
        self.is_ready.clear()
        self.logger.success(__stop_msg__)

    def _callback(self, msg):
        # self.is_busy.set()
        self.pre_hook(msg).handle(msg).post_hook(msg)
        self.last_active_time = time.perf_counter()
        return msg

    def msg_callback(self, msg: 'jina_pb2.Message') -> Optional['jina_pb2.Message']:
        """Callback function after receiving the message

        When nothing is returned then the nothing is send out via :attr:`zmqlet.sock_out`.
        """
        try:
            return self._callback(msg)
        except NoExplicitMessage:
            # silent and do not propagade message anymore
            # 1. wait partial message to be finished
            # 2. dealer send a control message and no need to go on
            pass

    def loop_body(self):
        """The body of the request loop

        .. note::

            Class inherited from :class:`BasePea` must override this function. And add
            :meth:`set_ready` when your loop body is started
        """
        self.load_plugins()
        self.load_executor()
        self.zmqlet = Zmqlet(self.args, logger=self.logger)
        self.set_ready()

        while True:
            # t_loop_start = time.perf_counter()
            msg = self.zmqlet.recv_message(callback=self.msg_callback)
            # t_callback = time.perf_counter()

            if msg:
                self.zmqlet.send_message(msg)

                self.save_executor(self.args.dump_interval)
                self.check_memory_watermark()
                # self.is_busy.clear()
            # t_loop_end = time.perf_counter()
            # self.logger.info(f'handle {(t_callback - t_loop_start) / (t_loop_end - t_loop_start):2.2f}')

    def load_plugins(self):
        if self.args.py_modules:
            from ..helper import PathImporter
            PathImporter.add_modules(*self.args.py_modules)

    def loop_teardown(self):
        """Stop the request loop """
        if hasattr(self, 'executor'):
            if not self.args.exit_no_dump:
                self.save_executor(dump_interval=0)
            self.executor.close()
        if hasattr(self, 'zmqlet'):
            if self.request_type == 'ControlRequest' and \
                    self.request.command == jina_pb2.Request.ControlRequest.TERMINATE:
                # the last message is a terminate request
                # return it and tells the client everything is now closed.
                self.zmqlet.send_message(self.message)
            self.zmqlet.close()

    def run(self):
        """Start the request loop of this BasePea. It will listen to the network protobuf message via ZeroMQ. """
        try:
            self.post_init()
            self.loop_body()
        except RequestLoopEnd:
            self.logger.info('break from the event loop')
        except ExecutorFailToLoad:
            self.logger.error('can not start a executor from %s' % self.args.yaml_path)
        except MemoryOverHighWatermark:
            self.logger.error(
                'memory usage %d GB is above the high-watermark: %d GB' % (used_memory(), self.args.memory_hwm))
        except UnknownControlCommand as ex:
            self.logger.error(ex, exc_info=True)
        except DriverNotInstalled:
            self.logger.error('no driver is installed to this pea, this pea will do nothing')
        except NoDriverForRequest:
            self.logger.error(f'no matched driver for {self.request_type} request, '
                              f'this pea is either badly configured or it is not configured to handle {self.request_type} request')
        except KeyboardInterrupt:
            self.logger.warning('user cancel the process')
        except zmq.error.ZMQError:
            self.logger.error('zmqlet can not be initiated')
        except Exception as ex:
            self.logger.error('unknown exception: %s' % str(ex), exc_info=True)
        finally:
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

    def close(self):
        """Gracefully close this pea and release all resources """
        if self.is_ready.is_set() and hasattr(self, 'ctrl_addr'):
            return send_ctrl_message(self.ctrl_addr, jina_pb2.Request.ControlRequest.TERMINATE,
                                     timeout=self.args.timeout_ctrl)

    @property
    def status(self):
        """Send the control signal ``STATUS`` to itself and return the status """
        if self.is_ready.is_set() and getattr(self, 'ctrl_addr'):
            return send_ctrl_message(self.ctrl_addr, jina_pb2.Request.ControlRequest.STATUS,
                                     timeout=self.args.timeout_ctrl)

    def start(self):
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
                self.logger.critical(f'fail to start {self.__class__} with name {self.name}')
            return self
        else:
            raise TimeoutError(
                f'{self.__class__} with name {self.name} can not be initialized after {_timeout * 1e3}ms')

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
