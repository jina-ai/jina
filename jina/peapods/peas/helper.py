import multiprocessing
import threading
from functools import partial

from ...enums import RuntimeBackendType


def _get_event(obj):
    if isinstance(obj, threading.Thread):
        return threading.Event()
    elif isinstance(obj, multiprocessing.Process):
        return multiprocessing.Event()
    else:
        raise TypeError(
            f'{obj} is not an instance of "threading.Thread" nor "multiprocessing.Process"'
        )


class ConditionalEvent:
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


class PeaType(type):
    """Type of :class:`Pea`, metaclass of :class:`BasePea`."""

    _dct = {}

    def __new__(cls, name, bases, dct):
        """
        Create and register a new class with this meta class.

        :param name: name of the :class:`Pea`
        :param bases: bases of :class:`Pea`
        :param dct: arguments dictionary
        :return: registered class
        """
        _cls = super().__new__(cls, name, bases, dct)
        PeaType._dct.update(
            {name: {'cls': cls, 'name': name, 'bases': bases, 'dct': dct}}
        )
        return _cls

    def __call__(cls, *args, **kwargs) -> 'PeaType':
        """
        change runtime backend

        :param args: arguments
        :param kwargs: keyword arguments
        :return: Call self as a function.
        """
        # switch to the new backend
        _cls = {
            RuntimeBackendType.THREAD: threading.Thread,
            RuntimeBackendType.PROCESS: multiprocessing.Process,
        }.get(getattr(args[0], 'runtime_backend', RuntimeBackendType.THREAD))

        # rebuild the class according to mro
        for c in cls.mro()[-2::-1]:
            arg_cls = PeaType._dct[c.__name__]['cls']
            arg_name = PeaType._dct[c.__name__]['name']
            arg_dct = PeaType._dct[c.__name__]['dct']
            _cls = super().__new__(arg_cls, arg_name, (_cls,), arg_dct)

        return type.__call__(_cls, *args, **kwargs)
