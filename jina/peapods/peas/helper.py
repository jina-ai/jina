import multiprocessing
import threading
from copy import deepcopy
from functools import partial
from typing import Union, TYPE_CHECKING

from ... import __default_host__
from ...enums import GatewayProtocolType, RuntimeBackendType
from ...hubble.helper import is_valid_huburi
from ...hubble.hubio import HubIO

if TYPE_CHECKING:
    from argparse import Namespace


def _get_event(obj) -> Union[multiprocessing.Event, threading.Event]:
    if isinstance(obj, threading.Thread):
        return threading.Event()
    elif isinstance(obj, multiprocessing.Process) or isinstance(
        obj, multiprocessing.context.ForkProcess
    ):
        return multiprocessing.Event()
    elif isinstance(obj, multiprocessing.context.SpawnProcess):
        return multiprocessing.get_context('spawn').Event()
    else:
        raise TypeError(
            f'{obj} is not an instance of "threading.Thread" nor "multiprocessing.Process"'
        )


class ConditionalEvent:
    """
    :class:`ConditionalEvent` provides a common interface to an event (multiprocessing or threading event)
    that gets triggered when any of the events provided in input is triggered (OR logic)

    :param backend_runtime: The runtime type to decide which type of Event to instantiate
    :param events_list: The list of events that compose this composable event
    """

    def __init__(self, backend_runtime: RuntimeBackendType, events_list):
        super().__init__()
        self.event = None
        if backend_runtime == RuntimeBackendType.THREAD:
            self.event = threading.Event()
        else:
            self.event = multiprocessing.synchronize.Event(
                ctx=multiprocessing.get_context()
            )
        self.event_list = events_list
        for e in events_list:
            self._setup(e, self._state_changed)

        self._state_changed()

    def _state_changed(self):
        bools = [e.is_set() for e in self.event_list]
        if any(bools):
            self.event.set()
        else:
            self.event.clear()

    def _custom_set(self, e):
        e._set()
        e._state_changed()

    def _custom_clear(self, e):
        e._clear()
        e._state_changed()

    def _setup(self, e, changed_callback):
        e._set = e.set
        e._clear = e.clear
        e._state_changed = changed_callback
        e.set = partial(self._custom_set, e)
        e.clear = partial(self._custom_clear, e)


def update_runtime_cls(args, copy=False) -> 'Namespace':
    """Get runtime_cls as a string from args

    :param args: pea/pod namespace args
    :param copy: True if args shouldn't be modified in-place
    :return: runtime class as a string
    """
    _args = deepcopy(args) if copy else args
    gateway_runtime_dict = {
        GatewayProtocolType.GRPC: 'GRPCRuntime',
        GatewayProtocolType.WEBSOCKET: 'WebSocketRuntime',
        GatewayProtocolType.HTTP: 'HTTPRuntime',
    }
    if (
        _args.runtime_cls not in gateway_runtime_dict.values()
        and _args.host != __default_host__
        and not _args.disable_remote
    ):
        _args.runtime_cls = 'JinadRuntime'
        # NOTE: remote pea would also create a remote workspace which might take alot of time.
        # setting it to -1 so that wait_start_success doesn't fail
        _args.timeout_ready = -1
    if _args.runtime_cls == 'ZEDRuntime' and _args.uses.startswith('docker://'):
        _args.runtime_cls = 'ContainerRuntime'
    if _args.runtime_cls == 'ZEDRuntime' and is_valid_huburi(_args.uses):
        _hub_args = deepcopy(_args)
        _hub_args.uri = _args.uses
        _hub_args.no_usage = True
        _args.uses = HubIO(_hub_args).pull()

        if _args.uses.startswith('docker://'):
            _args.runtime_cls = 'ContainerRuntime'

    if hasattr(_args, 'protocol'):
        _args.runtime_cls = gateway_runtime_dict[_args.protocol]

    return _args
