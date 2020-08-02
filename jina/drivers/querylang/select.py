__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple

from . import QueryLangDriver

if False:
    from ...proto import jina_pb2


class ExcludeQL(QueryLangDriver):
    """Clean some fields from the chunk-level protobuf to reduce the total size of the request
    """

    def __init__(self, fields: Tuple, *args, **kwargs):
        """

        :param fields: the pruned field names in tuple
        """
        super().__init__(*args, **kwargs)
        if isinstance(fields, str):
            self._fields = {fields, }
        else:
            self._fields = set(fields)

        # for deleting field in a recursive structure, postorder is safer
        self.recursion_order = 'post'

    def _apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        for k in self.fields:
            doc.ClearField(k)


class SelectQL(ExcludeQL):
    def _apply(self, doc: 'jina_pb2.Document', *args, **kwargs):
        for k in doc.DESCRIPTOR.fields_by_name.keys():
            if k not in self.fields:
                doc.ClearField(k)


# ChunkPruneDriver: pruned=('embedding', 'buffer', 'blob', 'text')
# DocPruneDriver: pruned=('chunks', 'buffer')

class ExcludeReqQL(ExcludeQL):
    """Clean up request from the protobuf message to reduce the total size of the message

        This is often useful when the proceeding Pods require only a signal, not the full message.
    """

    def __call__(self, *args, **kwargs):
        for k in self.fields:
            self.msg.ClearField(k)


class SelectReqQL(ExcludeReqQL):
    def __call__(self, *args, **kwargs):
        for k in self.msg.DESCRIPTOR.fields_by_name.keys():
            if k not in self.fields:
                self.msg.ClearField(k)
