from typing import Iterable

from .document import DocumentArray

if False:
    from ..document import Document


class ChunkArray(DocumentArray):
    """
    :class:`ChunkArray` inherits from :class:`DocumentArray`.
    It's a subset of Documents.

    :param docs_proto: List of sub-documents (i.e chunks) of `reference_doc`
    :type docs_proto: :class:`Document`
    :param reference_doc: Reference :class:`Document` for the sub-documents
    :type reference_doc: :class:`Document`
    """

    def __init__(self, docs_proto, reference_doc: 'Document'):
        super().__init__(docs_proto)
        self._ref_doc = reference_doc

    def append(self, document: 'Document', **kwargs) -> 'Document':
        """Add a sub-document (i.e chunk) to the current Document.

        :param document: Sub-document to be appended
        :type document: :class:`Document`
        :param kwargs: additional keyword arguments
        :return: the newly added sub-document in :class:`Document` view
        :rtype: :class:`Document`

        .. note::
            Comparing to :attr:`DocumentArray.append()`, this method adds more safeguard to
            make sure the added chunk is legit.
        """

        from ..document import Document

        c = self._docs_proto.add()
        c.CopyFrom(document.proto)
        chunk = Document(c)

        chunk.set_attrs(
            parent_id=self._ref_doc.id, granularity=self.granularity, **kwargs
        )

        if not chunk.mime_type:
            chunk.mime_type = self._ref_doc.mime_type
        chunk.update_content_hash()
        return chunk

    def extend(self, iterable: Iterable['Document']) -> None:
        """
        Extend the :class:`DocumentArray` by appending all the items from the iterable.

        :param iterable: the iterable of Documents to extend this array with
        """
        for doc in iterable:
            self.append(doc)
        num_siblings = len(self)
        for doc in self:
            doc.siblings = num_siblings

    @property
    def reference_doc(self) -> 'Document':
        """
        Get the document that :class:`ChunkArray` belongs to.

        :return: reference doc
        """
        return self._ref_doc

    @property
    def granularity(self) -> int:
        """
        Get granularity of all document in this array.

        :return: granularity
        """
        return self._ref_doc.granularity + 1

    @property
    def adjacency(self) -> int:
        """
        Get adjacency of all document in this array.

        :return: adjacency
        """
        return self._ref_doc.adjacency
