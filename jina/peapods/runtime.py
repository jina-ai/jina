import argparse
import multiprocessing
import threading
from multiprocessing.synchronize import Event
from typing import Dict, Union

from .zmq import send_ctrl_message, Zmqlet
from ..enums import PeaRoleType
from ..excepts import PeaFailToStart

from .. import __ready_msg__, __stop_msg__
from ..helper import typename
from ..logging import JinaLogger
from . import Pea

__all__ = ['RuntimeMeta', 'RunTime']


def _get_event(obj: 'RunTimeSupport') -> Event:
    if isinstance(obj, threading.Thread):
        return threading.Event()
    elif isinstance(obj, multiprocessing.Process):
        return multiprocessing.Event()
    else:
        raise NotImplementedError


def _make_or_event(obj: 'RunTimeSupport', *events) -> Event:
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


class RuntimeMeta(type):
    """Meta class of :class:`BasePea` to enable switching between ``thread`` and ``process`` backend. """
    _dct = {}

    def __new__(cls, name, bases, dct):
        _cls = super().__new__(cls, name, bases, dct)
        RuntimeMeta._dct.update({name: {'cls': cls,
                                        'name': name,
                                        'bases': bases,
                                        'dct': dct}})
        return _cls

    def __call__(cls, *args, **kwargs) -> 'RuntimeMeta':
        # switch to the new backend
        _cls = {
            'thread': threading.Thread,
            'process': multiprocessing.Process,
        }.get(getattr(args[0], 'runtime', 'thread'))

        # rebuild the class according to mro
        for c in cls.mro()[-2::-1]:
            arg_cls = RuntimeMeta._dct[c.__name__]['cls']
            arg_name = RuntimeMeta._dct[c.__name__]['name']
            arg_dct = RuntimeMeta._dct[c.__name__]['dct']
            _cls = super().__new__(arg_cls, arg_name, (_cls,), arg_dct)

        return type.__call__(_cls, *args, **kwargs)


class RunTime(metaclass=RuntimeMeta):
    def __init__(self, args: Union['argparse.Namespace', Dict]):
        self.args = args
        self.name = self.__class__.__name__

        self.is_ready_event = _get_event(self)
        self.is_shutdown = _get_event(self)
        self.ready_or_shutdown = _make_or_event(self, self.is_ready_event, self.is_shutdown)
        self.is_shutdown.clear()

        if isinstance(self.args, argparse.Namespace):
            if self.args.name:
                self.name = f'support-{self.args.name}'
            elif self.args.role == PeaRoleType.PARALLEL:
                self.name = f'support-{self.name}-{self.args.pea_id}'

            self.ctrl_addr, self.ctrl_with_ipc = Zmqlet.get_ctrl_address(self.args.host, self.args.port_ctrl,
                                                                         self.args.ctrl_with_ipc)
            self.logger = JinaLogger(self.name,
                                     log_id=self.args.log_id,
                                     log_config=self.args.log_config)
        else:
            self.logger = JinaLogger(self.name)

        self.pea = Pea(args, allow_remote=True)

    def set_ready(self, *args, **kwargs):
        """Set the status of the pea to ready """
        self.is_ready_event.set()
        self.logger.success(__ready_msg__)

    def unset_ready(self, *args, **kwargs):
        """Set the status of the pea to shutdown """
        self.is_ready_event.clear()
        self.logger.success(__stop_msg__)

    def run(self):
        """Start the request loop of this BasePea. It will listen to the network protobuf message via ZeroMQ. """
        try:
            with Pea(self.args) as pea:
                # TODO: set_ready in different coroutine checking status as it is done for `ContainerPea` (here zmq
                #  loop has not started)
                self.set_ready()
                pea.run()
        finally:
            # if an exception occurs this unsets ready and shutting down
            self.unset_ready()
            self.is_shutdown.set()

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
                # return too early and the shutdown is set, means something fails!!
                self.logger.critical(f'fail to start {typename(self)} with name {self.name}, '
                                     f'this often means the executor used in the pod is not valid')
                raise PeaFailToStart
            return self
        else:
            raise TimeoutError(
                f'{typename(self)} with name {self.name} can not be initialized after {_timeout * 1e3}ms')

    @property
    def status(self):
        """Send the control signal ``STATUS`` to itself and return the status """
        return send_ctrl_message(self.ctrl_addr, 'STATUS', timeout=self.args.timeout_ctrl)

    def send_terminate_signal(self):
        """Send a terminate signal to the Pea supported by this Runtime """
        return send_ctrl_message(self.ctrl_addr, 'TERMINATE', timeout=self.args.timeout_ctrl)

    def close(self) -> None:
        self.send_terminate_signal()
        self.pea.is_shutdown.wait()
        if not self.pea.daemon:
            self.logger.close()
            self.pea.join()

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
