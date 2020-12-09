from . import BasePod


class MutablePod(BasePod):
    """A :class:`MutablePod` is a pod where all peas and their connections are given"""

    def _parse_args(self, args):
        return args
