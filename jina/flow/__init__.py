from .base import BaseFlow
from ..clients.mixin import PostMixin


class Flow(PostMixin, BaseFlow):
    """The synchronous version of :class:`AsyncFlow`.

    For proper usage see `this guide` <https://docs.jina.ai/chapters/flow/index.html>
    """

    def dump(self, pod_name: str, dump_path: str, shards: int, timeout=-1):
        """Emit a Dump request to a specific Pod
        :param shards: the nr of shards in the dump
        :param dump_path: the path to which to dump
        :param pod_name: the name of the pod
        :param timeout: time to wait (seconds)
        """
        self.post(
            on='/dump',
            parameters={'dump_path': dump_path, 'shards': shards},
            target_peapod=pod_name,
        )
