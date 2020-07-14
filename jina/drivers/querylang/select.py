__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple

from .. import BaseRecursiveDriver

if False:
    from ...proto import jina_pb2


class ExcludeDriver(BaseRecursiveDriver):
    """Clean some fields from the chunk-level protobuf to reduce the total size of the request

    For example,

        - "chunk" level removed fields can be ``embedding``, ``buffer``, ``blob``, ``text``.
        - "doc" level removed fields can be ``chunks``, ``buffer``
        - "request" level is often useful when the proceeding Pods require only a signal, not the full message.
    """

    def __init__(self, keys: Tuple, *args, **kwargs):
        """

        :param keys: the pruned field names in tuple
        """
        super().__init__(*args, **kwargs)
        if isinstance(keys, str):
            self.keys = {keys, }
        else:
            self.keys = set(keys)

        # for deleting field in a recursive structure, postorder is safer
        self.recursion_order = 'post'

    def apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        for k in self.keys:
            doc.ClearField(k)


class SelectDriver(ExcludeDriver):
    def apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        for k in doc.DESCRIPTOR.fields_by_name.keys():
            if k not in self.keys:
                doc.ClearField(k)


# ChunkPruneDriver: pruned=('embedding', 'buffer', 'blob', 'text')
# DocPruneDriver: pruned=('chunks', 'buffer')

class ReqExcludeDriver(ExcludeDriver):
    """Clean up request from the protobuf message to reduce the total size of the message

        This is often useful when the proceeding Pods require only a signal, not the full message.
    """

    def __call__(self, *args, **kwargs):
        for k in self.keys:
            self.msg.ClearField(k)


class ReqSelectDriver(ReqExcludeDriver):
    def __call__(self, *args, **kwargs):
        for k in self.msg.DESCRIPTOR.fields_by_name.keys():
            if k not in self.keys:
                self.msg.ClearField(k)
