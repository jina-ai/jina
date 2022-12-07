"""Decorators and wrappers designed for wrapping :class:`BaseExecutor` functions. """
import functools
import inspect
import os
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Sequence, Union

from jina import __cache_path__
from jina.helper import iscoroutinefunction
from jina.importer import ImportExtensions

if TYPE_CHECKING:  # pragma: no cover
    from jina import DocumentArray


@functools.lru_cache()
def _get_locks_root() -> Path:
    locks_root = Path(os.path.join(__cache_path__, 'locks'))

    if not locks_root.exists():
        locks_root.mkdir(parents=True, exist_ok=True)

    return locks_root


def avoid_concurrent_lock_cls(cls):
    """Wraps a function to lock a filelock for concurrent access with the name of the class to which it applies, to avoid deadlocks
    :param cls: the class to which is applied, only when the class corresponds to the instance type, this filelock will apply
    :return: the wrapped function
    """

    def avoid_concurrent_lock_wrapper(func: Callable) -> Callable:
        """Wrap the function around a File Lock to make sure that the function is run by a single replica in the same machine
        :param func: the function to decorate
        :return: the wrapped function
        """

        @functools.wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            if func.__name__ != '__init__':
                raise TypeError(
                    'this decorator should only be used on __init__ method of an executor'
                )

            if self.__class__ == cls:
                with ImportExtensions(
                    required=False,
                    help_text=f'FileLock is needed to guarantee non-concurrent initialization of replicas in the '
                    f'same machine.',
                ):
                    import filelock

                    locks_root = _get_locks_root()

                    lock_file = locks_root.joinpath(f'{self.__class__.__name__}.lock')

                    file_lock = filelock.FileLock(lock_file, timeout=-1)

                with file_lock:
                    f = func(self, *args, **kwargs)
                return f
            else:
                return func(self, *args, **kwargs)

        return arg_wrapper

    return avoid_concurrent_lock_wrapper


def _init_requests_by_class(cls):
    """
    To allow inheritance and still have coherent usage of `requests`. Makes sure that a child class inherits requests from parents

    :param cls: The class.
    """
    if not hasattr(cls, 'requests_by_class'):
        cls.requests_by_class = {}

    if cls.__name__ not in cls.requests_by_class:
        cls.requests_by_class[cls.__name__] = {}

        def _inherit_from_parent_class_inner(cls_):
            for parent_class in cls_.__bases__:
                parent_dict = cls.requests_by_class.get(parent_class.__name__, {})
                for k, v in parent_dict.items():
                    if k not in cls.requests_by_class[cls.__name__]:
                        cls.requests_by_class[cls.__name__][k] = v
                _inherit_from_parent_class_inner(parent_class)

        # assume that `requests` is called when importing class, so parent classes will be processed before
        # inherit all the requests from parents
        _inherit_from_parent_class_inner(cls)


def requests(
    func: Optional[
        Callable[
            [
                'DocumentArray',
                Dict,
                'DocumentArray',
                List['DocumentArray'],
                List['DocumentArray'],
            ],
            Optional[Union['DocumentArray', Dict]],
        ]
    ] = None,
    *,
    on: Optional[Union[str, Sequence[str]]] = None,
):
    """
    `@requests` defines the endpoints of an Executor. It has a keyword `on=` to define the endpoint.

    A class method decorated with plain `@requests` (without `on=`) is the default handler for all endpoints.
    That means, it is the fallback handler for endpoints that are not found.

    EXAMPLE USAGE

    .. code-block:: python

        from jina import Executor, requests, Flow
        from docarray import Document


        # define Executor with custom `@requests` endpoints
        class MyExecutor(Executor):
            @requests(on='/index')
            def index(self, docs, **kwargs):
                print(docs)  # index docs here

            @requests(on=['/search', '/query'])
            def search(self, docs, **kwargs):
                print(docs)  # perform search here

            @requests  # default/fallback endpoint
            def foo(self, docs, **kwargs):
                print(docs)  # process docs here


        f = Flow().add(uses=MyExecutor)  # add your Executor to a Flow
        with f:
            f.post(
                on='/index', inputs=Document(text='I am here!')
            )  # send doc to `index` method
            f.post(
                on='/search', inputs=Document(text='Who is there?')
            )  # send doc to `search` method
            f.post(
                on='/query', inputs=Document(text='Who is there?')
            )  # send doc to `search` method
            f.post(on='/bar', inputs=Document(text='Who is there?'))  # send doc to `foo` method

    :param func: the method to decorate
    :param on: the endpoint string, by convention starts with `/`
    :return: decorated function
    """
    from jina import __args_executor_func__, __default_endpoint__

    class FunctionMapper:
        def __init__(self, fn):
            arg_spec = inspect.getfullargspec(fn)
            if not arg_spec.varkw and not __args_executor_func__.issubset(
                arg_spec.args
            ):
                raise TypeError(
                    f'{fn} accepts only {arg_spec.args} which is fewer than expected, '
                    f'please add `**kwargs` to the function signature.'
                )

            if iscoroutinefunction(fn):

                @functools.wraps(fn)
                async def arg_wrapper(
                    executor_instance, *args, **kwargs
                ):  # we need to get the summary from the executor, so we need to access the self
                    return await fn(executor_instance, *args, **kwargs)

                self.fn = arg_wrapper
            else:

                @functools.wraps(fn)
                def arg_wrapper(
                    executor_instance, *args, **kwargs
                ):  # we need to get the summary from the executor, so we need to access the self
                    return fn(executor_instance, *args, **kwargs)

                self.fn = arg_wrapper

        def __set_name__(self, owner, name):
            _init_requests_by_class(owner)
            self.fn.class_name = owner.__name__
            if isinstance(on, (list, tuple)):
                for o in on:
                    owner.requests_by_class[owner.__name__][o] = self.fn
            else:
                owner.requests_by_class[owner.__name__][
                    on or __default_endpoint__
                ] = self.fn

            setattr(owner, name, self.fn)

    if func:
        return FunctionMapper(func)
    else:
        return FunctionMapper


def monitor(
    *,
    name: Optional[str] = None,
    documentation: Optional[str] = None,
):
    """
    Decorator and context manager that allows monitoring of an Executor.

    You can access these metrics by enabling
    monitoring on your Executor. It will track the time spent calling the function and the number of times it has been
    called. Under the hood it will create a prometheus Summary : https://prometheus.io/docs/practices/histograms/.

    EXAMPLE USAGE

        As decorator

        .. code-block:: python

            from jina import Executor, monitor


            class MyExecutor(Executor):
                @requests  # `@requests` are monitored automatically
                def foo(self, docs, *args, **kwargs):
                    ...
                    self.my_method()
                    ...

                # custom metric for `my_method`
                @monitor(name='metric_name', documentation='useful information goes here')
                def my_method(self):
                    ...

        As context manager

        .. code-block:: python

            from jina import Executor, requests


            class MyExecutor(Executor):
                @requests  # `@requests` are monitored automatically
                def foo(self, docs, *args, **kwargs):
                    ...
                    # custom metric for code block
                    with self.monitor('metric_name', 'useful information goes here'):
                        docs = process(docs)

        To enable the defined :meth:`monitor` blocks, enable monitoring on the Flow level

        .. code-block:: python

            from jina import Flow

            f = Flow(monitoring=True, port_monitoring=9090).add(
                uses=MyExecutor, port_monitoring=9091
            )
            with f:
                ...

    :warning: Don't use this decorator in combination with the @request decorator. @request's are already monitored.

    :param name: the name of the metrics, by default it is based on the name of the method it decorates
    :param documentation:  the description of the metrics, by default it is based on the name of the method it decorates

    :return: decorator which takes as an input a single callable
    """

    def _decorator(func: Callable):
        name_ = name if name else f'{func.__name__}_seconds'
        documentation_ = (
            documentation
            if documentation
            else f'Time spent calling method {func.__name__}'
        )

        @functools.wraps(func)
        def _f(self, *args, **kwargs):
            with self.monitor(name_, documentation_):
                return func(self, *args, **kwargs)

        return _f

    return _decorator
