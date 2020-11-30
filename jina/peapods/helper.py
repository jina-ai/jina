import multiprocessing
import threading
from multiprocessing.synchronize import Event
from typing import Any


def _get_event(obj: Any) -> Event:
    if isinstance(obj, threading.Thread):
        return threading.Event()
    elif isinstance(obj, multiprocessing.Process):
        return multiprocessing.Event()
    else:
        raise NotImplementedError


def _make_or_event(obj: Any, *events) -> Event:
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
