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
