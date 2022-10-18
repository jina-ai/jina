import functools
import inspect
import typing
from typing import Optional, Union

from jina.helper import convert_tuple_to_list

if typing.TYPE_CHECKING:
    from prometheus_client.context_managers import Timer
    from prometheus_client import Summary

from contextlib import nullcontext


def _get_summary_time_context_or_null(
    summary_metric: Optional['Summary'],
) -> Union[nullcontext, 'Timer']:
    """
    helper function to either get a time context or a nullcontext if the summary metric is None
    :param summary_metric: An optional metric
    :return: either a Timer context or a nullcontext
    """
    return summary_metric.time() if summary_metric else nullcontext()


def wrap_func(cls, func_lst, wrapper, **kwargs):
    """Wrapping a class method only once, inherited but not overridden method will not be wrapped again

    :param cls: class
    :param func_lst: function list to wrap
    :param wrapper: the wrapper
    :param kwargs: extra wrapper kwargs
    """
    for f_name in func_lst:
        if hasattr(cls, f_name) and all(
            getattr(cls, f_name) != getattr(i, f_name, None) for i in cls.mro()[1:]
        ):
            setattr(cls, f_name, wrapper(getattr(cls, f_name), **kwargs))


def store_init_kwargs(
    func: typing.Callable, taboo: Optional[typing.Set] = None
) -> typing.Callable:
    """Mark the args and kwargs of :func:`__init__` later to be stored via :func:`save_config` in YAML
    :param func: the function to decorate
    :param taboo: class taboo set of parameters
    :return: the wrapped function
    """
    taboo = taboo or {}

    @functools.wraps(func)
    def arg_wrapper(self, *args, **kwargs):
        if func.__name__ != '__init__':
            raise TypeError('this decorator should only be used on __init__ method')
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
