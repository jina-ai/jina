__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple

from . import BaseRecursiveDriver


class PruneDriver(BaseRecursiveDriver):
    """Clean some fields from the chunk-level protobuf to reduce the total size of the request

    For example,

        - "chunk" level removed fields can be ``embedding``, ``buffer``, ``blob``, ``text``.
        - "doc" level removed fields can be ``chunks``, ``buffer``
        - "request" level is often useful when the proceeding Pods require only a signal, not the full message.
    """

    def __init__(self, pruned: Tuple, *args, **kwargs):
        """

        :param pruned: the pruned field names in tuple
        :param level: index level "chunk", "doc", "request" or "all"
        """
        super().__init__(*args, **kwargs)
        if isinstance(pruned, str):
            self.pruned = (pruned,)
        else:
            self.pruned = pruned

        # for deleting field in a recursive structure, postorder is safer
        self._order = 'post'

    def apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        for k in self.pruned:
            doc.ClearField(k)


class ChunkPruneDriver(PruneDriver):
    """Clean some fields from the chunk-level protobuf to reduce the total size of the request

    Removed fields are ``embedding``, ``buffer``, ``blob``, ``text``.
    """

    def __init__(self, pruned=('embedding', 'buffer', 'blob', 'text'), *args, **kwargs):
        super().__init__(pruned, *args, **kwargs)


class DocPruneDriver(PruneDriver):
    """Clean some fields from the doc-level protobuf to reduce the total size of request

    Removed fields are ``chunks``, ``buffer``
    """

    def __init__(self, pruned=('chunks', 'buffer'), *args, **kwargs):
        super().__init__(pruned, *args, **kwargs)


class ReqPruneDriver(PruneDriver):
    """Clean up request from the protobuf message to reduce the total size of the message

        This is often useful when the proceeding Pods require only a signal, not the full message.
    """

    def __call__(self, *args, **kwargs):
        for k in self.pruned:
            self.msg.ClearField(k)
