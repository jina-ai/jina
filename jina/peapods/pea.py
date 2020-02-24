import multiprocessing
import threading
import time
from collections import defaultdict
from typing import Dict, List

from .zmq import send_ctrl_message, Zmqlet
from ..drivers import Driver
from ..drivers.helper import routes2str, add_route
from ..excepts import WaitPendingMessage, ExecutorFailToLoad, MemoryOverHighWatermark, UnknownControlCommand, \
    EventLoopEnd, \
    DriverNotInstalled, NoRequestHandler
from ..executors import BaseExecutor
from ..logging import profile_logger, get_logger
from ..logging.profile import used_memory, TimeDict
from ..proto import jina_pb2

__all__ = ['PeaMeta', 'Pea']

if False:
    # fix type-hint complain for sphinx and flake
    import argparse


class PeaMeta(type):
    """Meta class of :class:`Pea` to enable switching between ``thread`` and ``process`` backend. """
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
            'process': multiprocessing.Process
        }[args[0].parallel_runtime]

        # rebuild the class according to mro
        for c in cls.mro()[-2::-1]:
            arg_cls = PeaMeta._dct[c.__name__]['cls']
            arg_name = PeaMeta._dct[c.__name__]['name']
            arg_dct = PeaMeta._dct[c.__name__]['dct']
            _cls = super().__new__(arg_cls, arg_name, (_cls,), arg_dct)

        return type.__call__(_cls, *args, **kwargs)


class Pea(metaclass=PeaMeta):
    """Pea is an unary service unit which provides network interface and
    communicates with others via protobuf and ZeroMQ
    """

    def _get_event(self):
        if isinstance(self, threading.Thread):
            return threading.Event()
        elif isinstance(self, multiprocessing.Process):
            return multiprocessing.Event()
        else:
            raise NotImplementedError

    def __init__(self, args: 'argparse.Namespace', replica_id: int = None):
        """ Create a new :class:`Pea` object

        :param args: the arguments received from the CLI
        :param replica_id: the id used to separate the storage of each pea, only used when ``args.separate_storage=True``
        """
        super().__init__()
        self.args = args
        self.name = args.name or args.driver_group or self.__class__.__name__
        self.logger = get_logger(self.name, **vars(args))
        self.is_ready = self._get_event()
        self.is_event_loop = self._get_event()

        self.ctrl_addr, self.ctrl_with_ipc = Zmqlet.get_ctrl_address(args)
        self.last_dump_time = time.perf_counter()
        self.replica_id = replica_id

        self._timer = TimeDict()

        self._request = None
        self._message = None
        self._prev_requests = None
        self._prev_messages = None
        self._pending_msgs = defaultdict(list)  # type: Dict[str, List]

    def register_msg(self, msg: 'jina_pb2.Message') -> None:
        """Register the current message to this pea

        :param msg: the message received
        """
        self._request = getattr(msg.request, msg.request.WhichOneof('body'))
        self._message = msg
        msg_type = type(self._request)

        if self.args.num_part > 1 and msg_type != jina_pb2.Request.ControlRequest:
            # do not wait for control request
            req_id = msg.envelope.request_id
            self._pending_msgs[req_id].append(msg)
            num_req = len(self._pending_msgs[req_id])

            if num_req == self.args.num_part:
                self._prev_messages = self._pending_msgs.pop(req_id)
                self._prev_requests = [getattr(v.request, v.request.WhichOneof('body')) for v in self._prev_messages]
            else:
                self.logger.debug('waiting for %d/%d %s messages' % (num_req, self.args.num_part, msg_type))
                raise WaitPendingMessage
        else:
            self._prev_requests = None
            self._prev_messages = None

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
    def prev_messages(self) -> List['jina_pb2.Message']:
        """Get all previous messages that has the same ``request_id``

        This returns ``None`` when ``num_part=1``.
        """
        return self._prev_messages

    def load_driver(self):
        """Load driver to this Pea, specified by ``driver_yaml_path`` and ``driver`` from CLI arguments

        """
        self.driver = Driver(self, self.args.driver_yaml_path, self.args.driver_group)
        self.driver.verify()

    def load_executor(self):
        """Load the executor to this Pea, specified by ``exec_yaml_path`` CLI argument.

        .. note::
            A non-executor :class:`Pea` is possible but then :func:`load_driver` must be implemented. Otherwise this
            Pea will have no actual logic at all.

        """
        if self.args.exec_yaml_path:
            try:
                self.executor = BaseExecutor.load_config(self.args.exec_yaml_path,
                                                         self.args.separated_workspace, self.replica_id)
            except FileNotFoundError:
                raise ExecutorFailToLoad('can not executor from %s' % self.args.exec_yaml_path)
        else:
            self.logger.warning('this Pea has no executor attached, you may want to double-check '
                                'if it is a mistake or on purpose (using this Pea as router/map-reduce)')

    def save_executor(self, dump_interval: int = 0):
        """Save the contained executor

        :param dump_interval: the time interval for saving
        """
        if self.args.read_only:
            self.logger.info('executor is not saved as "read_only" is set to true for this Pea')
        elif not hasattr(self, 'executor'):
            self.logger.debug('this Pea contains no executor, no need to save')
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

    def pre_hook(self, msg: 'jina_pb2.Message') -> None:
        msg_type = msg.request.WhichOneof('body')
        self.logger.info('received "%s" from %s' % (msg_type, routes2str(msg, flag_current=True)))
        add_route(msg.envelope, self.name, self.args.identity)

    def post_hook(self, msg: 'jina_pb2.Message') -> None:
        msg.envelope.routes[-1].end_time.GetCurrentTime()

    def run(self):
        """Start the eventloop of this Pea. It will listen to the network protobuf message via ZeroMQ. """
        with Zmqlet(self.args, logger=self.logger) as zmqlet:

            def _callback(msg):
                try:
                    self.pre_hook(msg)
                    self.register_msg(msg)
                    self.executor.apply()
                    self.post_hook(msg)
                    return msg
                except WaitPendingMessage:
                    pass
                except EventLoopEnd:
                    zmqlet.send_message(msg)
                    raise EventLoopEnd

            try:
                self.post_init()
                self.is_event_loop.set()
                self.logger.critical('ready and listening')
                self.is_ready.set()

                while self.is_event_loop.is_set():
                    msg = zmqlet.recv_message(callback=_callback)
                    if msg is not None:
                        zmqlet.send_message(msg)
                    else:
                        continue

                    self.save_executor(self.args.dump_interval)
                    self.check_memory_watermark()
            except EventLoopEnd:
                self.logger.info('break from the event loop')
            except ExecutorFailToLoad:
                self.logger.error('component can not be correctly loaded, terminated')
            except MemoryOverHighWatermark:
                self.logger.error(
                    'memory usage %d GB is above the high-watermark: %d GB' % (used_memory(), self.args.memory_hwm))
            except UnknownControlCommand as ex:
                self.logger.error(ex, exc_info=True)
            except DriverNotInstalled:
                self.logger.error('no driver is installed to this service, this service will do nothing')
            except NoRequestHandler:
                self.logger.error('no matched handler for the request, this service is badly configured')
            except KeyboardInterrupt:
                self.logger.warning('user cancel the process')
            except Exception as ex:
                self.logger.error('unknown exception: %s' % str(ex), exc_info=True)
            finally:
                self.is_ready.set()
                self.is_event_loop.clear()

                if not self.args.exit_no_dump:
                    self.save_executor(dump_interval=0)
                if hasattr(self, 'executor'):
                    self.executor.close()

        self.logger.critical('terminated')

    def check_memory_watermark(self):
        """Check the memory watermark """
        if used_memory() > self.args.memory_hwm > 0:
            raise MemoryOverHighWatermark

    def post_init(self):
        """Post initializer after the start of the eventloop via :func:`run`, so that they can be kept in the same
        process/thread as the eventloop.

        """
        self.load_executor()
        self.load_driver()

    def close(self):
        """Gracefully close this pea and release all resources """
        if self.is_event_loop.is_set():
            return send_ctrl_message(self.ctrl_addr, jina_pb2.Request.ControlRequest.TERMINATE,
                                     timeout=self.args.timeout)

    @property
    def status(self):
        """Send the control signal ``STATUS`` to itself and return the status """
        return send_ctrl_message(self.ctrl_addr, jina_pb2.Request.ControlRequest.STATUS,
                                 timeout=self.args.timeout)

    def __enter__(self):
        self.start()
        self.is_ready.wait()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
