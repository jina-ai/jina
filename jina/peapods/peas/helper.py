import multiprocessing
import threading
from functools import partial
from typing import Union

from ...enums import RuntimeBackendType


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
