"""Decorators and wrappers designed for wrapping :class:`BaseExecutor` functions. """
import functools
import inspect
from functools import wraps
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Sequence, Union

from jina.helper import convert_tuple_to_list, iscoroutinefunction
from jina.serve.executors.metas import get_default_metas

if TYPE_CHECKING:
    from jina import DocumentArray


def wrap_func(cls, func_lst, wrapper):
    """Wrapping a class method only once, inherited but not overridden method will not be wrapped again

    :param cls: class
    :param func_lst: function list to wrap
    :param wrapper: the wrapper
    """
    for f_name in func_lst:
        if hasattr(cls, f_name) and all(
            getattr(cls, f_name) != getattr(i, f_name, None) for i in cls.mro()[1:]
        ):
            setattr(cls, f_name, wrapper(getattr(cls, f_name)))


def store_init_kwargs(func: Callable) -> Callable:
    """Mark the args and kwargs of :func:`__init__` later to be stored via :func:`save_config` in YAML
    :param func: the function to decorate
    :return: the wrapped function
    """

    @wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        if func.__name__ != '__init__':
            raise TypeError(
                'this decorator should only be used on __init__ method of an executor'
            )
        taboo = {'self', 'args', 'kwargs', 'metas', 'requests', 'runtime_args'}
        _defaults = get_default_metas()
        taboo.update(_defaults.keys())
        all_pars = inspect.signature(func).parameters
        tmp = {k: v.default for k, v in all_pars.items() if k not in taboo}
        tmp_list = [k for k in all_pars.keys() if k not in taboo]
        # set args by aligning tmp_list with arg values
        for k, v in zip(tmp_list, args):
            tmp[k] = v
        # set kwargs
        for k, v in kwargs.items():
            if k in tmp:
                tmp[k] = v

        if hasattr(self, '_init_kwargs_dict'):
            self._init_kwargs_dict.update(tmp)
        else:
            self._init_kwargs_dict = tmp
        convert_tuple_to_list(self._init_kwargs_dict)
        f = func(self, *args, **kwargs)
        return f

    return arg_wrapper


def requests(
    func: Callable[
        [
            'DocumentArray',
            Dict,
            'DocumentArray',
            List['DocumentArray'],
            List['DocumentArray'],
        ],
        Optional[Union['DocumentArray', Dict]],
    ] = None,
    *,
    on: Optional[Union[str, Sequence[str]]] = None,
):
    """
    `@requests` defines when a function will be invoked. It has a keyword `on=` to define the endpoint.

    A class method decorated with plan `@requests` (without `on=`) is the default handler for all endpoints.
    That means, it is the fallback handler for endpoints that are not found.

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
            self.fn.class_name = owner.__name__
            if not hasattr(owner, 'requests'):
                owner.requests = {}

            if isinstance(on, (list, tuple)):
                for o in on:
                    owner.requests[o] = self.fn
            else:
                owner.requests[on or __default_endpoint__] = self.fn

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
    `@monitor()` allow to monitor internal method of your executor. You can access these metrics by enabling the
    monitoring on your Executor. It will track the time spend calling the function and the number of times it has been
    called. Under the hood it will create a prometheus Summary : https://prometheus.io/docs/practices/histograms/.

    :warning: Don't use this decorator with the @request decorator as it already handle monitoring under the hood

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
            metric = self.get_metrics(name_, documentation_)

            if metric:
                with metric.time():
                    return func(self, *args, **kwargs)
            else:
                return func(self, *args, **kwargs)

        return _f

    return _decorator
