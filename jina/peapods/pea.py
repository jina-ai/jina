import argparse
import multiprocessing
import threading
import time
from collections import defaultdict
from queue import Empty
from typing import Dict, List

from .zmq import send_ctrl_message, Zmqlet
from .. import __ready_msg__, __stop_msg__
from ..drivers.helper import routes2str, add_route
from ..excepts import WaitPendingMessage, ExecutorFailToLoad, MemoryOverHighWatermark, UnknownControlCommand, \
    RequestLoopEnd, \
    DriverNotInstalled, NoDriverForRequest
from ..executors import BaseExecutor
from ..logging import profile_logger, get_logger
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


class BasePea(metaclass=PeaMeta):
    """BasePea is an unary service unit which provides network interface and
    communicates with others via protobuf and ZeroMQ
    """

    def __init__(self, args: 'argparse.Namespace'):
        """ Create a new :class:`BasePea` object

        :param args: the arguments received from the CLI
        :param replica_id: the id used to separate the storage of each pea, only used when ``args.separate_storage=True``
        """
        super().__init__()
        self.args = args
        self.name = self.__class__.__name__

        self.is_ready = _get_event(self)

        self.last_dump_time = time.perf_counter()

        self._timer = TimeDict()

        self._request = None
        self._message = None
        self._prev_requests = None
        self._prev_messages = None
        self._pending_msgs = defaultdict(list)  # type: Dict[str, List]

        if isinstance(args, argparse.Namespace):
            if args.name:
                self.name = args.name
            if args.replica_id >= 0:
                self.name = '%s-%d' % (self.name, args.replica_id)
            self.ctrl_addr, self.ctrl_with_ipc = Zmqlet.get_ctrl_address(args)
            self.logger = get_logger(self.name, **vars(args))
        else:
            self.logger = get_logger(self.name)

    def handle(self, msg: 'jina_pb2.Message') -> 'BasePea':
        """Register the current message to this pea, so that all message-related properties are up-to-date, including
        :attr:`request`, :attr:`prev_requests`, :attr:`message`, :attr:`prev_messages`. And then call the executor to handle
        this message.

        :param msg: the message received
        """
        self._request = getattr(msg.request, msg.request.WhichOneof('body'))
        self._message = msg
        req_type = type(self._request)

        if self.args.num_part > 1 and (req_type != jina_pb2.Request.ControlRequest
                                       or (req_type == jina_pb2.Request.ControlRequest
                                           and self._request.command == jina_pb2.Request.ControlRequest.DRYRUN)):
            # do not wait for control request
            req_id = msg.envelope.request_id
            self._pending_msgs[req_id].append(msg)
            num_req = len(self._pending_msgs[req_id])

            if num_req == self.args.num_part:
                self._prev_messages = self._pending_msgs.pop(req_id)
                self._prev_requests = [getattr(v.request, v.request.WhichOneof('body')) for v in self._prev_messages]
            else:
                raise WaitPendingMessage
            self.logger.info('collected %d/%d parts of %r' % (num_req, self.args.num_part, req_type))
        else:
            self._prev_requests = None
            self._prev_messages = None

        self.executor(self.request_type)
        return self

    @property
    def request(self) -> 'jina_pb2.Request':
        """Get the current request body inside the protobuf message"""
        return self._request

    @property
    def prev_requests(self) -> List['jina_pb2.Request']:
        """Get all previous requests that has the same ``request_id``

        This returns ``None`` when ``num_part=1``.
        """
        return self._prev_requests

    @property
    def message(self) -> 'jina_pb2.Message':
        """Get the current protobuf message to be processed"""
        return self._message

    @property
    def request_type(self) -> str:
        return self._request.__class__.__name__

    @property
    def prev_messages(self) -> List['jina_pb2.Message']:
        """Get all previous messages that has the same ``request_id``

        This returns ``None`` when ``num_part=1``.
        """
        return self._prev_messages

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

    def save_executor(self, dump_interval: int = 0):
        """Save the contained executor

        :param dump_interval: the time interval for saving
        """
        if self.args.read_only:
            self.logger.info('executor is not saved as "read_only" is set to true for this BasePea')
        elif not hasattr(self, 'executor'):
            self.logger.debug('this BasePea contains no executor, no need to save')
        elif ((time.perf_counter() - self.last_dump_time) > self.args.dump_interval > 0) or dump_interval <= 0:
            if self.executor.save():
                self.logger.info('dumped changes to the executor, %3.0fs since last the save'
                                 % (time.perf_counter() - self.last_dump_time))
                self.last_dump_time = time.perf_counter()
            else:
                self.logger.info('executor says there is nothing to save')

            profile_logger.info({'service': self.name,
                                 'profile': self._timer.accum_time,
                                 'timestamp_start': self._timer.start_time,
                                 'timestamp_end': self._timer.end_time})

            self._timer.reset()

    def pre_hook(self, msg: 'jina_pb2.Message') -> 'BasePea':
        """Pre-hook function, what to do after first receiving the message """
        msg_type = msg.request.WhichOneof('body')
        self.logger.info('received "%s" from %s' % (msg_type, routes2str(msg, flag_current=True)))
        add_route(msg.envelope, self.name, self.args.identity)
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

    def loop_body(self):
        """The body pf the request loop """

        def _callback(msg):
            try:
                self.pre_hook(msg).handle(msg).post_hook(msg)
                return msg
            except WaitPendingMessage:
                pass

        self.load_executor()
        self.zmqlet = Zmqlet(self.args, logger=self.logger)
        self.set_ready()

        while True:
            msg = self.zmqlet.recv_message(callback=_callback)
            if msg is not None:
                self.zmqlet.send_message(msg)
            else:
                continue

            self.save_executor(self.args.dump_interval)
            self.check_memory_watermark()

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
            self.logger.error('can not executor from %s' % self.args.yaml_path)
        except MemoryOverHighWatermark:
            self.logger.error(
                'memory usage %d GB is above the high-watermark: %d GB' % (used_memory(), self.args.memory_hwm))
        except UnknownControlCommand as ex:
            self.logger.error(ex, exc_info=True)
        except DriverNotInstalled:
            self.logger.error('no driver is installed to this service, this service will do nothing')
        except NoDriverForRequest:
            self.logger.error('no matched handler for the request, this service is badly configured')
        except KeyboardInterrupt:
            self.logger.warning('user cancel the process')
        except Exception as ex:
            self.logger.error('unknown exception: %s' % str(ex), exc_info=True)
        finally:
            self.loop_teardown()
            self.unset_ready()

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
        _timeout = getattr(self.args, 'timeout_ready', 5e3) / 1e3
        if self.is_ready.wait(_timeout):
            return self
        else:
            raise TimeoutError('this BasePea (name=%s) can not be initialized after %dms' % (self.name, _timeout * 1e3))

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


