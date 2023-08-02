import multiprocessing
from copy import deepcopy
from functools import partial
from typing import TYPE_CHECKING

from hubble.executor.helper import is_valid_huburi
from hubble.executor.hubio import HubIO

from jina.enums import PodRoleType
from jina.parsers.helper import _update_gateway_args

if TYPE_CHECKING:  # pragma: no cover
    from argparse import Namespace


def _get_event(obj) -> multiprocessing.Event:
    if isinstance(obj, multiprocessing.Process) or isinstance(
        obj, multiprocessing.context.ForkProcess
    ):
        return multiprocessing.Event()
    elif isinstance(obj, multiprocessing.context.SpawnProcess):
        return multiprocessing.get_context('spawn').Event()
    else:
        raise TypeError(f'{obj} is not an instance of "multiprocessing.Process"')


class ConditionalEvent:
    """
    :class:`ConditionalEvent` provides a common interface to an event (multiprocessing or threading event)
    that gets triggered when any of the events provided in input is triggered (OR logic)

    :param events_list: The list of events that compose this composable event
    """

    def __init__(self, events_list):
        super().__init__()
        self.event = None
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


def update_runtime_cls(args) -> 'Namespace':
    """Get runtime_cls as a string from args

    :param args: pod/deployment namespace args
    :return: runtime class as a string
    """
    _args = args

    if _args.runtime_cls == 'WorkerRuntime' and is_valid_huburi(_args.uses):
        _hub_args = deepcopy(_args)
        _hub_args.uri = _args.uses
        _hub_args.no_usage = True
        _args.uses = HubIO(_hub_args).pull()

    if hasattr(_args, 'protocol') and _args.pod_role == PodRoleType.GATEWAY:
        _update_gateway_args(_args)
    if _args.pod_role == PodRoleType.HEAD:
        _args.runtime_cls = 'HeadRuntime'

    return _args
