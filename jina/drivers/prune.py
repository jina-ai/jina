__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple

from . import BaseDriver


class PruneDriver(BaseDriver):
    """Clean some fields from the chunk-level protobuf to reduce the total size of the request

    For example,

        - "chunk" level removed fields can be ``embedding``, ``buffer``, ``blob``, ``text``.
        - "doc" level removed fields can be ``chunks``, ``buffer``
        - "request" level is often useful when the proceeding Pods require only a signal, not the full message.
    """

    def __init__(self, pruned: Tuple, level: str, *args, **kwargs):
        """

        :param pruned: the pruned field names in tuple
        :param level: index level "chunk", "doc", "request" or "all"
        """
        super().__init__(*args, **kwargs)
        if isinstance(pruned, str):
            self.pruned = (pruned,)
        else:
            self.pruned = pruned
        self.level = level

    def __call__(self, *args, **kwargs):
        if self.level == 'chunk':
            for d in self.req.docs:
                for c in d.chunks:
                    for k in self.pruned:
                        c.ClearField(k)
        elif self.level == 'doc':
            for d in self.req.docs:
                for k in self.pruned:
                    d.ClearField(k)
        elif self.level == 'request':
            for k in self.pruned:
                self.msg.ClearField(k)
        elif self.level == 'all':
            for d in self.req.docs:
                for c in d.chunks:
                    for k in self.pruned:
                        c.ClearField(k)
                for k in self.pruned:
                    d.ClearField(k)
            for k in self.pruned:
                self.msg.ClearField(k)
        else:
            raise TypeError(f'level={self.level} is not supported, must choose from "chunk" or "doc" ')


class ChunkPruneDriver(PruneDriver):
    """Clean some fields from the chunk-level protobuf to reduce the total size of the request

    Removed fields are ``embedding``, ``buffer``, ``blob``, ``text``.
    """

    def __init__(self, pruned=('embedding', 'buffer', 'blob', 'text'), level='chunk', *args, **kwargs):
        super().__init__(pruned, level, *args, **kwargs)


class DocPruneDriver(PruneDriver):
    """Clean some fields from the doc-level protobuf to reduce the total size of request

    Removed fields are ``chunks``, ``buffer``
    """

    def __init__(self, pruned=('chunks', 'buffer'), level='doc', *args, **kwargs):
        super().__init__(pruned, level, *args, **kwargs)


class ReqPruneDriver(PruneDriver):
    """Clean up request from the protobuf message to reduce the total size of the message

        This is often useful when the proceeding Pods require only a signal, not the full message.
    """

    def __init__(self, pruned=('request',), level='request', *args, **kwargs):
        super().__init__(pruned, level, *args, **kwargs)
