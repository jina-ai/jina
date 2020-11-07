__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
import multiprocessing
import os
import threading
import time
from multiprocessing.synchronize import Event
from queue import Empty
from typing import Dict, Optional, Union

import zmq

from jina import __unable_to_load_pretrained_model_msg__
from .zmq import send_ctrl_message, Zmqlet, ZmqStreamlet
from .. import __ready_msg__, __stop_msg__
from ..enums import PeaRoleType, SkipOnErrorType
from ..excepts import NoExplicitMessage, ExecutorFailToLoad, MemoryOverHighWatermark, DriverError, PeaFailToStart, \
    ModelCheckpointNotExist, ChainedPodException
from ..executors import BaseExecutor
from ..helper import is_valid_local_config_source
from ..logging import JinaLogger
from ..logging.profile import used_memory, TimeDict
from ..logging.queue import clear_queues
from ..proto import jina_pb2
from ..proto.message import ProtoMessage, LazyRequest

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
        self.is_pretrained_model_exception = _get_event(self)
        self.ready_or_shutdown = _make_or_event(self, self.is_ready_event, self.is_shutdown)
        self.is_shutdown.clear()
        self.is_pretrained_model_exception.clear()

        self.last_active_time = time.perf_counter()
        self.last_dump_time = time.perf_counter()

        self._timer = TimeDict()

        self._request = None
        self._message = None

        if isinstance(self.args, argparse.Namespace):
            self.daemon = args.daemon
            if self.args.name:
                self.name = self.args.name
            if self.args.role == PeaRoleType.PARALLEL:
                self.name = '%s-%d' % (self.name, self.args.pea_id)
            self.ctrl_addr, self.ctrl_with_ipc = Zmqlet.get_ctrl_address(self.args)
            if self.args.name:
                # everything in this Pea (process) will use the same name for display the log
                os.environ['JINA_POD_NAME'] = self.args.name
            self.logger = JinaLogger(self.name, **vars(self.args))
        else:
            self.logger = JinaLogger(self.name)

    def __str__(self):
        r = self.name
        if getattr(self, 'executor', None):
            r += f'({str(self.executor)})'
        return r

    def handle(self, msg: 'ProtoMessage') -> 'BasePea':
        """Register the current message to this pea, so that all message-related properties are up-to-date, including
        :attr:`request`, :attr:`prev_requests`, :attr:`message`, :attr:`prev_messages`. And then call the executor to handle
        this message if its envelope's  status is not ERROR, else skip handling of message.

        :param msg: the message received
        """
        if msg.envelope.status.code != jina_pb2.Status.ERROR or self.args.skip_on_error < SkipOnErrorType.HANDLE:
            self.executor(self.request_type)
        else:
            raise ChainedPodException
        return self

    @property
    def is_idle(self) -> bool:
        """Return ``True`` when current time is ``max_idle_time`` seconds late than the last active time"""
        return (time.perf_counter() - self.last_active_time) > self.args.max_idle_time

    @property
    def request(self) -> 'LazyRequest':
        """Get the current request body inside the protobuf message"""
        return self._request

    @property
    def message(self) -> 'ProtoMessage':
        """Get the current protobuf message to be processed"""
        return self._message

    @property
    def request_type(self) -> str:
        return self._message.envelope.request_type

    @property
    def log_iterator(self):
        """Get the last log using iterator """
        from ..logging.queue import __log_queue__
        while self.is_ready_event.is_set():
            try:
                yield __log_queue__.get_nowait()
            except Empty:
                pass

    def load_executor(self):
        """Load the executor to this BasePea, specified by ``uses`` CLI argument.

        """
        if self.args.uses:
            try:
                self.executor = BaseExecutor.load_config(
                    self.args.uses if is_valid_local_config_source(self.args.uses) else self.args.uses_internal,
                    self.args.separated_workspace, self.args.pea_id)
                self.executor.attach(pea=self)
            except FileNotFoundError:
                raise ExecutorFailToLoad
            except ModelCheckpointNotExist as exception:
                self.is_pretrained_model_exception.set()
                raise exception
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

    def pre_hook(self, msg: 'ProtoMessage') -> 'BasePea':
        """Pre-hook function, what to do after first receiving the message """
        self.logger.info(f'received {msg.envelope.request_type} from {msg.colored_route}')
        msg.add_route(self.name, self.args.identity)
        self._request = msg.request
        self._message = msg
        return self

    def post_hook(self, msg: 'ProtoMessage') -> 'BasePea':
        """Post-hook function, what to do before handing out the message """
        # self.logger.critical(f'is message used: {msg.request.is_used}')
        self.last_active_time = time.perf_counter()
        self.save_executor(self.args.dump_interval)
        self.check_memory_watermark()
        msg.update_timestamp()
        if self.args.num_part > 1:
            msg.num_part = self.args.num_part
        return self

    def set_ready(self, *args, **kwargs):
        """Set the status of the pea to ready """
        self.is_ready_event.set()
        self.logger.success(__ready_msg__)

    def unset_ready(self, *args, **kwargs):
        """Set the status of the pea to shutdown """
        self.is_ready_event.clear()
        self.logger.success(__stop_msg__)

    def _callback(self, msg: 'ProtoMessage'):
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

    def msg_callback(self, msg: 'ProtoMessage') -> Optional['ProtoMessage']:
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
            self.zmqlet.send_message(msg)

    def loop_body(self):
        """The body of the request loop

        .. note::

            Class inherited from :class:`BasePea` must override this function. And add
            :meth:`set_ready` when your loop body is started
        """
        self.load_plugins()
        self.load_executor()
        self.zmqlet = ZmqStreamlet(self.args, logger=self.logger)
        self.set_ready()
        self.zmqlet.start(self.msg_callback)

    def load_plugins(self):
        if self.args.py_modules:
            from ..helper import PathImporter
            PathImporter.add_modules(*self.args.py_modules)

    def loop_teardown(self):
        """Stop the request loop """
        if hasattr(self, 'zmqlet'):
            self.zmqlet.close()

    def run(self):
        """Start the request loop of this BasePea. It will listen to the network protobuf message via ZeroMQ. """
        try:
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
        except ModelCheckpointNotExist:
            self.logger.critical(__unable_to_load_pretrained_model_msg__)
            self.is_pretrained_model_exception.set()
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
            send_ctrl_message(self.ctrl_addr, jina_pb2.Request.ControlRequest.TERMINATE,
                              timeout=self.args.timeout_ctrl)

    @property
    def status(self):
        """Send the control signal ``STATUS`` to itself and return the status """
        if self.is_ready_event.is_set() and getattr(self, 'ctrl_addr'):
            return send_ctrl_message(self.ctrl_addr, jina_pb2.Request.ControlRequest.STATUS,
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
                self.logger.critical(f'fail to start {self.__class__} with name {self.name}, '
                                     f'this often means the executor used in the pod is not valid')
                if self.is_pretrained_model_exception.is_set():
                    raise ModelCheckpointNotExist
                else:
                    raise PeaFailToStart
            return self
        else:
            raise TimeoutError(
                f'{self.__class__} with name {self.name} can not be initialized after {_timeout * 1e3}ms')

    def __enter__(self) -> 'BasePea':
        return self.start()

    def close(self) -> None:
        self.send_terminate_signal()
        self.is_shutdown.wait()
        if not self.daemon:
            clear_queues()
            self.logger.close()
            self.join()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
