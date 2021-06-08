from functools import wraps
from typing import List

from ..enums import FlowBuildLevel
from ..excepts import FlowBuildLevelError

# noinspection PyUnreachableCode
if False:
    from . import Flow


def allowed_levels(levels: List['FlowBuildLevel']):
    """Annotate a function so that it requires certain build level to run.

    Example:

    .. highlight:: python
    .. code-block:: python

        @build_required(FlowBuildLevel.RUNTIME)
        def foo():
            print(1)

    :param levels: required build level to run this function.
    :return: annotated function
    """

    def __build_level(func):
        @wraps(func)
        def arg_wrapper(self, *args, **kwargs):
            if hasattr(self, '_build_level'):
                if self._build_level in levels:
                    return func(self, *args, **kwargs)
                else:
                    raise FlowBuildLevelError(
                        f'build_level check failed for {func!r}, required level: {levels}, actual level: {self._build_level}'
                    )
            else:
                raise AttributeError(f'{self!r} has no attribute "_build_level"')

        return arg_wrapper

    return __build_level


def _hanging_pods(op_flow: 'Flow') -> List[str]:
    """
    :param op_flow: the Flow we're operating on
    :return: names of hanging Pods (nobody recv from them) in the Flow.
    """
    all_needs = {v for p in op_flow._pod_nodes.values() for v in p.needs}
    all_names = {p for p in op_flow._pod_nodes.keys()}
    # all_names is always a superset of all_needs
    return list(all_names.difference(all_needs))
