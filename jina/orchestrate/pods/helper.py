import multiprocessing
import threading
from copy import deepcopy
from functools import partial
from typing import TYPE_CHECKING, Callable, Dict, Optional, Union

from grpc import RpcError

from jina.enums import GatewayProtocolType, PodRoleType, RuntimeBackendType
from jina.hubble.helper import is_valid_huburi
from jina.hubble.hubio import HubIO
from jina.serve.networking import GrpcConnectionPool
from jina.types.request.control import ControlRequest

if TYPE_CHECKING:
    from argparse import Namespace


def _get_worker(
    args, target: Callable, kwargs: Dict, name: Optional[str] = None
) -> Union['threading.Thread', 'multiprocessing.Process']:
    return {
        RuntimeBackendType.THREAD: threading.Thread,
        RuntimeBackendType.PROCESS: multiprocessing.Process,
    }.get(getattr(args, 'runtime_backend', RuntimeBackendType.THREAD))(
        target=target, name=name, kwargs=kwargs, daemon=True
    )


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

    :param args: pod/deployment namespace args
    :param copy: True if args shouldn't be modified in-place
    :return: runtime class as a string
    """
    _args = deepcopy(args) if copy else args
    gateway_runtime_dict = {
        GatewayProtocolType.GRPC: 'GRPCGatewayRuntime',
        GatewayProtocolType.WEBSOCKET: 'WebSocketGatewayRuntime',
        GatewayProtocolType.HTTP: 'HTTPGatewayRuntime',
    }
    if _args.runtime_cls == 'WorkerRuntime' and is_valid_huburi(_args.uses):
        _hub_args = deepcopy(_args)
        _hub_args.uri = _args.uses
        _hub_args.no_usage = True
        _args.uses = HubIO(_hub_args).pull()

    if hasattr(_args, 'protocol'):
        _args.runtime_cls = gateway_runtime_dict[_args.protocol]
    if _args.pod_role == PodRoleType.HEAD:
        _args.runtime_cls = 'HeadRuntime'

    return _args


def is_ready(address: str) -> bool:
    """
    TODO: make this async
    Check if status is ready.
    :param address: the address where the control message needs to be sent
    :return: True if status is ready else False.
    """

    try:
        GrpcConnectionPool.send_request_sync(ControlRequest('STATUS'), address)
    except RpcError:
        return False
    return True
