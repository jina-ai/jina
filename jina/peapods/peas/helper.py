import multiprocessing
import threading
from multiprocessing.synchronize import Event

from ...enums import RuntimeBackendType


def _get_event(obj) -> Event:
    if isinstance(obj, threading.Thread):
        return threading.Event()
    elif isinstance(obj, multiprocessing.Process):
        return multiprocessing.Event()
    else:
        raise TypeError(
            f'{obj} is not an instance of "threading.Thread" nor "multiprocessing.Process"'
        )


def _make_or_event(obj, *events) -> Event:
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
