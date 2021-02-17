__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Union, Tuple

from .. import QuerySetReader, RecursiveMixin, BaseRecursiveDriver

# noinspection PyUnreachableCode
if False:
    from ...types.sets import DocumentSet


class ExcludeQL(QuerySetReader, RecursiveMixin, BaseRecursiveDriver):
    """Clean some fields from the document-level protobuf to reduce the total size of the request
        Example::
        - !ExcludeQL
        with:
            fields:
                - chunks
                - buffer

        ExcludeQL will avoid `buffer` and `chunks` fields to be sent to the next `Pod`

        :param fields: the pruned field names in tuple
        :param traversal_paths: the traversal paths
        :param *args: *args
        :param **kwargs: **kwargs
    """

    def __init__(self, fields: Union[Tuple, str], traversal_paths: Tuple[str] = ('r',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)
        if isinstance(fields, str):
            self._fields = [fields]
        else:
            self._fields = [field for field in fields]

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs):
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

    def _apply_all(self, docs: 'DocumentSet', *args, **kwargs):
        for doc in docs:
            for k in doc.DESCRIPTOR.fields_by_name.keys():
                if k not in self.fields:
                    doc.ClearField(k)


class ExcludeReqQL(ExcludeQL):
    """Clean up request from the request-level protobuf message to reduce the total size of the message

        This is often useful when the proceeding Pods require only a signal, not the full message.
    """

    def __call__(self, *args, **kwargs):
        """


        .. # noqa: DAR102


        .. # noqa: DAR101
        """
        for k in self.fields:
            self.req.ClearField(k)


class SelectReqQL(ExcludeReqQL):
    """Clean up request from the request-level protobuf message to reduce the total size of the message, it works with the opposite
    logic as `:class:`ExcludeReqQL`


    .. # noqa: DAR101
    """

    def __call__(self, *args, **kwargs):
        """


        .. # noqa: DAR102


        .. # noqa: DAR101
        """
        for k in self.req.DESCRIPTOR.fields_by_name.keys():
            if k not in self.fields:
                self.req.ClearField(k)
