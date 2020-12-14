import argparse
import multiprocessing
import threading
from multiprocessing.synchronize import Event
from typing import Dict, Union

from jina.peapods.zmq import send_ctrl_message, Zmqlet
from jina.enums import PeaRoleType
from jina.excepts import PeaFailToStart

from jina.helper import typename
from jina.logging import JinaLogger

__all__ = ['RuntimeMeta', 'RunTime']


def _get_event(obj: 'RunTime') -> Event:
    if isinstance(obj, threading.Thread):
        return threading.Event()
    elif isinstance(obj, multiprocessing.Process):
        return multiprocessing.Event()
    else:
        raise NotImplementedError


def _make_or_event(obj: 'RunTime', *events) -> Event:
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
        super().__init__()
        self.args = args
        self.name = self.__class__.__name__  #: this is the process name

        self.is_ready_event = _get_event(self)
        self.is_shutdown = _get_event(self)
        self.ready_or_shutdown = _make_or_event(self, self.is_ready_event, self.is_shutdown)
        self.is_shutdown.clear()

        if 'daemon' in args:
            self.daemon = args.daemon
        if 'name' in self.args and self.args.name:
            self.name = f'support-{self.args.name}'
        if 'role' in self.args and self.args.role == PeaRoleType.PARALLEL:
            self.name = f'support-{self.args.name}-{self.args.pea_id}'
        if 'role' in self.args and self.args.role == PeaRoleType.HEAD:
            self.name = f'support-{self.args.name}-head'
        if 'role' in self.args and self.args.role == PeaRoleType.TAIL:
            self.name = f'support-{self.args.name}-tail'
        if 'host' in self.args and 'port_ctrl' in self.args and 'ctrl_with_ipc' in self.args:
            self.ctrl_addr, self.ctrl_with_ipc = Zmqlet.get_ctrl_address(self.args.host, self.args.port_ctrl,
                                                                         self.args.ctrl_with_ipc)

        if 'log_id' in self.args and 'log_config' in self.args:
            self.logger = JinaLogger(self.name,
                                     log_id=self.args.log_id,
                                     log_config=self.args.log_config)
        else:
            self.logger = JinaLogger(self.name)

    def run(self):
        raise NotImplementedError

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
                self.logger.critical(f'fails to start {typename(self)} with name {self.name}, '
                                     f'this often means the executor used in the pod is not valid')
                raise PeaFailToStart
            return self
        else:
            raise TimeoutError(
                f'{typename(self)} with name {self.name} can not be initialized after {_timeout * 1e3}ms')

    def set_ready(self):
        """Set the status of the pea to ready """
        self.is_ready_event.set()

    def unset_ready(self):
        """Set the status of the pea to shutdown """
        self.is_ready_event.clear()

    def set_shutdown(self):
        self.is_shutdown.set()

    @property
    def status(self):
        """Send the control signal ``STATUS`` to itself and return the status """
        return send_ctrl_message(self.ctrl_addr, 'STATUS', timeout=self.args.timeout_ctrl)

    @property
    def is_ready(self) -> bool:
        status = self.status
        return status and status.is_ready

    @property
    def is_idle(self) -> bool:
        raise NotImplementedError

    def send_terminate_signal(self):
        """Send a terminate signal to the Pea supported by this LocalRunTime """
        return send_ctrl_message(self.ctrl_addr, 'TERMINATE', timeout=self.args.timeout_ctrl)

    def close(self) -> None:
        self.send_terminate_signal()
        self.is_shutdown.wait()
        self.logger.close()
        if not self.daemon:
            self.join()

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
