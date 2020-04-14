from typing import Tuple

from . import BaseDriver


class BasePruneDriver(BaseDriver):
    """Base class for all prune drivers"""

    def __init__(self, pruned: Tuple, *args, **kwargs):
        """

        :param pruned: the pruned field names in tuple
        """
        super().__init__(*args, **kwargs)
        if isinstance(pruned, str):
            self.pruned = (pruned,)
        else:
            self.pruned = pruned


class ChunkPruneDriver(BasePruneDriver):
    """Clean some fields from the chunk-level protobuf to reduce the total size of the request

    Removed fields are ``embedding``, ``raw_bytes``, ``blob``, ``text``.
    """

    def __init__(self, pruned=('embedding', 'raw_bytes', 'blob', 'text'), *args, **kwargs):
        super().__init__(pruned, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            for c in d.chunks:
                for k in self.pruned:
                    c.ClearField(k)


class DocPruneDriver(BasePruneDriver):
    """Clean some fields from the doc-level protobuf to reduce the total size of request

    Removed fields are ``chunks``, ``raw_bytes``
    """

    def __init__(self, pruned=('chunks', 'raw_bytes'), *args, **kwargs):
        super().__init__(pruned, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            for k in self.pruned:
                d.ClearField(k)


class ReqPruneDriver(BasePruneDriver):
    """Clean up request from the protobuf message to reduce the total size of the message

        This is often useful when the proceeding Pods require only a signal, not the full message.
    """

    def __init__(self, pruned=('request',), *args, **kwargs):
        super().__init__(pruned, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        for k in self.pruned:
            self.msg.ClearField(k)
