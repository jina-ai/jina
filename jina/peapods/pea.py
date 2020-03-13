import multiprocessing
import os
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from .zmq import send_ctrl_message, Zmqlet
from .. import __ready_signal__, __default_host__
from ..clients.python import SpawnPeaPyClient
from ..drivers.helper import routes2str, add_route
from ..excepts import WaitPendingMessage, ExecutorFailToLoad, MemoryOverHighWatermark, UnknownControlCommand, \
    EventLoopEnd, \
    DriverNotInstalled, NoDriverForRequest
from ..executors import BaseExecutor
from ..helper import kwargs2list, valid_yaml_path
from ..logging import profile_logger, get_logger
from ..logging.profile import used_memory, TimeDict
from ..proto import jina_pb2

__all__ = ['PeaMeta', 'Pea', 'ContainerPea', 'get_pea']

# temporary fix for python 3.8 on macos where the default start is set to "spawn"
# https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods
_mp = multiprocessing.get_context('fork')

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
            'process': _mp.Process
        }[args[0].runtime]

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
    elif isinstance(obj, _mp.Process):
        return _mp.Event()
    else:
        raise NotImplementedError


class Pea(metaclass=PeaMeta):
    """Pea is an unary service unit which provides network interface and
    communicates with others via protobuf and ZeroMQ
    """

    def __init__(self, args: 'argparse.Namespace'):
        """ Create a new :class:`Pea` object

        :param args: the arguments received from the CLI
        :param replica_id: the id used to separate the storage of each pea, only used when ``args.separate_storage=True``
        """
        super().__init__()
        self.args = args
        self.name = args.name or self.__class__.__name__
        if args.replica_id >= 0:
            self.name = '%s-%d' % (self.name, args.replica_id)
        self.log_event = _get_event(self)
        self.is_ready = _get_event(self)
        self.is_event_loop = _get_event(self)
        self.logger = get_logger(self.name, **vars(args), log_event=self.log_event)

        self.ctrl_addr, self.ctrl_with_ipc = Zmqlet.get_ctrl_address(args)
        self.last_dump_time = time.perf_counter()

        self._timer = TimeDict()

        self._request = None
        self._message = None
        self._prev_requests = None
        self._prev_messages = None
        self._pending_msgs = defaultdict(list)  # type: Dict[str, List]

    def handle(self, msg: 'jina_pb2.Message') -> 'Pea':
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
        while self.is_event_loop.is_set():
            yield from self.last_log_record
        yield '%r has just been terminated, won\'t be able to track its log anymore' % self

    @property
    def last_log_record(self):
        """Yield the last log record if exist """
        if self.log_event.wait(.0001):
            yield self.log_event.record
            self.log_event.clear()

    def load_executor(self):
        """Load the executor to this Pea, specified by ``exec_yaml_path`` CLI argument.

        """
        if self.args.yaml_path:
            try:
                self.executor = BaseExecutor.load_config(self.args.yaml_path,
                                                         self.args.separated_workspace, self.args.replica_id)
                self.executor.attach(pea=self)
                # self.logger = get_logger('%s(%s)' % (self.name, self.executor.name), **vars(self.args))
            except FileNotFoundError:
                raise ExecutorFailToLoad('can not executor from %s' % self.args.yaml_path)
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

    def pre_hook(self, msg: 'jina_pb2.Message') -> 'Pea':
        """Pre-hook function, what to do after first receiving the message """
        msg_type = msg.request.WhichOneof('body')
        self.logger.info('received "%s" from %s' % (msg_type, routes2str(msg, flag_current=True)))
        add_route(msg.envelope, self.name, self.args.identity)
        return self

    def post_hook(self, msg: 'jina_pb2.Message') -> 'Pea':
        """Post-hook function, what to do before handing out the message """
        msg.envelope.routes[-1].end_time.GetCurrentTime()
        return self

    def set_ready(self):
        """Set the status of the pea to ready """
        self.is_ready.set()
        self.is_event_loop.set()
        self.logger.critical(__ready_signal__)

    def event_loop_start(self):
        """Start the event loop """
        with Zmqlet(self.args, logger=self.logger) as zmqlet:
            def _callback(msg):
                try:
                    self.pre_hook(msg).handle(msg).post_hook(msg)
                    return msg
                except WaitPendingMessage:
                    pass
                except EventLoopEnd:
                    zmqlet.send_message(msg)
                    raise EventLoopEnd

            self.set_ready()

            while self.is_event_loop.is_set():
                msg = zmqlet.recv_message(callback=_callback)
                if msg is not None:
                    zmqlet.send_message(msg)
                else:
                    continue

                self.save_executor(self.args.dump_interval)
                self.check_memory_watermark()

    def event_loop_stop(self):
        """Stop the event loop """
        if hasattr(self, 'executor'):
            if not self.args.exit_no_dump:
                self.save_executor(dump_interval=0)
            self.executor.close()

    def run(self):
        """Start the eventloop of this Pea. It will listen to the network protobuf message via ZeroMQ. """
        try:
            self.post_init()
            self.event_loop_start()
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
        except NoDriverForRequest:
            self.logger.error('no matched handler for the request, this service is badly configured')
        except KeyboardInterrupt:
            self.logger.warning('user cancel the process')
        except Exception as ex:
            self.logger.error('unknown exception: %s' % str(ex), exc_info=True)
        finally:
            # self.is_ready.set()
            self.event_loop_stop()
            self.is_event_loop.clear()

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

    def close(self):
        """Gracefully close this pea and release all resources """
        if self.is_event_loop.is_set():
            return send_ctrl_message(self.ctrl_addr, jina_pb2.Request.ControlRequest.TERMINATE,
                                     timeout=self.args.timeout)

    @property
    def status(self):
        """Send the control signal ``STATUS`` to itself and return the status """
        return send_ctrl_message(self.ctrl_addr, jina_pb2.Request.ControlRequest.STATUS,
                                 timeout=self.args.timeout_ctrl)

    def __enter__(self):
        self.start()
        if self.is_ready.wait(self.args.timeout_ready / 1000):
            return self
        else:
            raise TimeoutError('this Pea (name=%s) can not be initialized after %dms' % (self.name,
                                                                                         self.args.timeout_ready))

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class RemotePea(Pea):
    """A Pea that spawns another pea remotely """

    def __init__(self, args: 'argparse.Namespace'):
        if hasattr(args, 'host'):
            super().__init__(args)
            if args.host == __default_host__:
                self.logger.warning(f'you are using {self.__class__} locally by setting host to {args.host}, '
                                    f'are you sure about this?')
        else:
            raise ValueError(
                '%r requires "args.host" to be set, and it should not be %s' % (self.__class__, __default_host__))

    def post_init(self):
        pass

    def event_loop_start(self):
        self.remote_pea = SpawnPeaPyClient(self.args)
        self.remote_pea.start(self.set_ready)

    def event_loop_stop(self):
        if getattr(self, 'remote_pea', None):
            self.remote_pea.close()


class ContainerPea(Pea):
    """A Pea that wraps another "dockerized" Pea

    It requires a non-empty valid ``args.image``.
    """

    def __init__(self, args: 'argparse.Namespace'):
        if hasattr(args, 'image') and args.image:
            super().__init__(args)
        else:
            raise ValueError('%s requires "args.image" to be set' % self.__class__)
        self._container = None
        import docker
        self._client = docker.from_env()

    def post_init(self):
        non_defaults = {}
        from ..main.parser import set_pea_parser
        _defaults = vars(set_pea_parser().parse_args([]))
        # the image arg should be ignored otherwise it keeps using ContainerPea in the container
        # basically all args in Pea-docker arg group should be ignored.
        # this prevent setting containerPea twice
        taboo = {'image', 'entrypoint', 'volumes', 'pull_latest'}
        for k, v in vars(self.args).items():
            if k in _defaults and k not in taboo and _defaults[k] != v:
                non_defaults[k] = v

        if self.args.pull_latest:
            self._client.images.pull(self.args.image)

        _volumes = {}
        if self.args.yaml_path:
            if os.path.exists(self.args.yaml_path):
                # external YAML config, need to be volumed into the container
                non_defaults['yaml_path'] = '/' + os.path.basename(self.args.yaml_path)
                _volumes[os.path.abspath(self.args.yaml_path)] = {'bind': non_defaults['yaml_path'], 'mode': 'ro'}
            elif not valid_yaml_path(self.args.yaml_path):
                raise FileNotFoundError('yaml_path %s is not like a path, please check it' % self.args.yaml_path)
        if self.args.volumes:
            for p in self.args.volumes:
                Path(os.path.abspath(p)).mkdir(parents=True, exist_ok=True)
                _p = '/' + os.path.basename(p)
                _volumes[os.path.abspath(p)] = {'bind': _p, 'mode': 'rw'}

        _expose_port = [self.args.port_ctrl]
        if self.args.socket_in.is_bind:
            _expose_port.append(self.args.port_in)
        if self.args.socket_out.is_bind:
            _expose_port.append(self.args.port_out)

        from sys import platform
        if platform == "linux" or platform == "linux2":
            net_mode = 'host'
        else:
            net_mode = None

        _args = kwargs2list(non_defaults)
        self._container = self._client.containers.run(self.args.image, _args,
                                                      detach=True, auto_remove=True,
                                                      ports={'%d/tcp' % v: v for v in
                                                             _expose_port},
                                                      name=self.name,
                                                      volumes=_volumes,
                                                      network_mode=net_mode,
                                                      entrypoint=self.args.entrypoint,
                                                      # network='mynetwork',
                                                      # publish_all_ports=True
                                                      )
        # wait until the container is ready
        self.logger.info('waiting ready signal from the container')
        self.is_event_loop.set()

    def event_loop_start(self):
        """Direct the log from the container to local console """
        import docker

        logger = get_logger('🐳', **vars(self.args), fmt_str='🐳 %(message)s')
        try:
            for line in self._container.logs(stream=True):
                if self.is_event_loop.is_set():
                    msg = line.strip().decode()
                    # this is shabby, but it seems the only easy way to detect is_ready signal meanwhile
                    # print all error message when fails
                    if __ready_signal__ in msg:
                        self.is_ready.set()
                        self.logger.critical(__ready_signal__)
                    logger.info(line.strip().decode())
                else:
                    raise EventLoopEnd
        except docker.errors.NotFound:
            self.logger.error('the container can not be started, check your arguments, entrypoint')

    def event_loop_stop(self):
        """Stop the container """

        import docker

        if getattr(self, '_container', None):
            try:
                self._container.stop()
            except docker.errors.NotFound:
                self.logger.warning(
                    'the container is already shutdown (mostly because of some error inside the container)')
        if getattr(self, '_client', None):
            self._client.close()


def get_pea(args: 'argparse.Namespace', allow_remote: bool = True):
    """Initialize a :class:`Pea`, :class:`RemotePea` or :class:`ContainerPea`

    :param args: arguments from CLI
    :param allow_remote: allow start a :class:`RemotePea`
    """
    if allow_remote and args.host != __default_host__:
        return RemotePea(args)
    elif args.image:
        return ContainerPea(args)
    else:
        return Pea(args)
