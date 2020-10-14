__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable, Tuple

from .. import QuerySetReader, BaseRecursiveDriver

if False:
    from ...proto import jina_pb2


class ExcludeQL(QuerySetReader, BaseRecursiveDriver):
    """Clean some fields from the document-level protobuf to reduce the total size of the request
        Example::
        - !ExcludeQL
        with:
            fields:
                - chunks
                - buffer

        ExcludeQL will avoid `buffer` and `chunks` fields to be sent to the next `Pod`
    """

    def __init__(self, fields: Tuple, traversal_paths: Tuple[str] = ('c',), *args, **kwargs):
        """

        :param fields: the pruned field names in tuple
        """
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)
        if isinstance(fields, str):
            self._fields = {fields, }
        else:
            self._fields = set(fields)

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        for doc in docs:
            for k in self.fields:
                doc.ClearField(k)


class SelectQL(ExcludeQL):
    """Selects some fields from the chunk-level protobuf to reduce the total size of the request, it works with the opposite
    logic as `:class:`ExcludeQL`

        Example::
        - !SelectQL
        with:
            fields:
                - matches

        SelectQL will ensure that the `outgoing` documents only contain the field `matches`
    """

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        for doc in docs:
            for k in doc.DESCRIPTOR.fields_by_name.keys():
                if k not in self.fields:
                    doc.ClearField(k)


class ExcludeReqQL(ExcludeQL):
    """Clean up request from the request-level protobuf message to reduce the total size of the message

        This is often useful when the proceeding Pods require only a signal, not the full message.
    """

    def __call__(self, *args, **kwargs):
        for k in self.fields:
            self.msg.ClearField(k)


class SelectReqQL(ExcludeReqQL):
    """Clean up request from the request-level protobuf message to reduce the total size of the message, it works with the opposite
    logic as `:class:`ExcludeReqQL`
    """

    def __call__(self, *args, **kwargs):
        for k in self.msg.DESCRIPTOR.fields_by_name.keys():
            if k not in self.fields:
                self.msg.ClearField(k)
