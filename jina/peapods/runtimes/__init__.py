import argparse
import multiprocessing
import os
import threading
from multiprocessing.synchronize import Event

from ... import __stop_msg__
from ...excepts import RuntimeFailToStart
from ...helper import typename
from ...logging import JinaLogger

__all__ = ['BaseRuntime']


def _get_event(obj: 'BaseRuntime') -> Event:
    if isinstance(obj, threading.Thread):
        return threading.Event()
    elif isinstance(obj, multiprocessing.Process):
        return multiprocessing.Event()
    else:
        raise NotImplementedError


def _make_or_event(obj: 'BaseRuntime', *events) -> Event:
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
    """Meta class of :class:`BaseRuntime` to enable switching between ``thread`` and ``process`` backend. """
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


class BaseRuntime(metaclass=RuntimeMeta):
    """BaseRuntime is a process or thread providing the support to run different :class:`BaseRuntime` in different environments.
    It manages the lifetime of these `BaseRuntime` objects living in `Local`, `Remote`, or `Container` environment.

    Inherited classes must define their own `run` method that is the one that will be run in a separate process or thread than the main process
    """

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__()
        self.args = args
        self.name = self.args.name or self.__class__.__name__
        self.is_ready = _get_event(self)
        self.is_shutdown = _get_event(self)
        self.ready_or_shutdown = _make_or_event(self, self.is_ready, self.is_shutdown)
        self.logger = JinaLogger(self.name,
                                 log_id=self.args.log_id,
                                 log_config=self.args.log_config)
        self.runtime = Pea(args)

    def run(self):
        """ Method representing the process’s activity.

        .. note::
            If your overrided function,
            you MUST implement ``self.is_ready.set()`` to BEFORE you move into the forever loop.
        """

        def _finally():
            self.is_ready.clear()
            self.is_shutdown.set()
            self._unset_envs()

        self._set_envs()

        try:
            self.runtime.setup()
        except Exception as ex:
            self.logger.error(f'{ex!r} during setup of {self.runtime!r}')
        else:
            self.is_ready.set()
            try:
                self.runtime.serve_forever()
            except KeyboardInterrupt:
                self.logger.info('interrupted by user')
            except (Exception, SystemError) as ex:
                self.logger.error(f'{ex!r} during serving of {self.runtime!r}', exc_info=True)

        try:
            self.runtime.teardown()
        except Exception as ex:
            self.logger.error(f'{ex!r} during teardown of {self.runtime!r}')
        finally:
            _finally()

    def start(self):
        """ Start the :class:`Runtime`’s activity.

        This must be called at most once per :class:`Runtime` object.
        It arranges for the :class:`Runtime`’s :meth:`run` method to be invoked in a separate process/thread.
        """
        super().start()  #: required here to call process/thread method
        _timeout = self.args.timeout_ready
        if _timeout <= 0:
            _timeout = None
        else:
            _timeout /= 1e3

        if self.ready_or_shutdown.wait(_timeout):
            if self.is_shutdown.is_set():
                # return too early and the shutdown is set, means something fails!!
                self.logger.critical(f'fails to start {typename(self)}:{self.name}, '
                                     f'this often means the executor used in the pod is not valid')
                raise RuntimeFailToStart
            else:
                self.logger.info(f'ready to listen')
        else:
            raise TimeoutError(
                f'{typename(self)}:{self.name} can not be initialized after {_timeout * 1e3}ms')

    def close(self) -> None:
        """Close this `Runtime` by sending a `terminate signal` to the managed `BaseRuntime`. Wait to
         be sure that the `BaseRuntime` is properly closed to join the parallel process """
        self.runtime.cancel()
        self.is_shutdown.wait()
        if not self.args.daemon:
            self.join()
        self.logger.success(__stop_msg__)
        self.logger.close()

    def _set_envs(self):
        """Set environment variable to this pea

        .. note::
            Please note that env variables are process-specific. Subprocess inherits envs from
            the main process. But Subprocess's envs do NOT affect the main process. It does NOT
            mess up user local system envs.

        .. warning::
            If you are using ``thread`` as backend, envs setting will likely be overidden by others
        """
        if self.args.env:
            if self.args.runtime == 'thread':
                self.logger.warning('environment variables should not be set when runtime="thread". '
                                    f'ignoring all environment variables: {self._envs}')
            else:
                for k, v in self.args.env.items():
                    os.environ[k] = v

    def _unset_envs(self):
        if self.args.env and self.args.runtime != 'thread':
            for k in self.args.env.keys():
                os.unsetenv(k)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
