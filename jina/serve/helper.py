import typing
from typing import Optional, Union

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
