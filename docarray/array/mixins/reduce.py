from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ...document import Document
    from ...helper import T


def _reduce_doc_props(doc1: 'Document', doc2: 'Document'):
    doc1_fields = set(
        field_descriptor.name for field_descriptor, _ in doc1._pb_body.ListFields()
    )
    doc2_fields = set(
        field_descriptor.name for field_descriptor, _ in doc2._pb_body.ListFields()
    )

    # update only fields that are set in doc2 and not set in doc1
    fields = doc2_fields - doc1_fields

    fields = fields - {'matches', 'chunks', 'id', 'parent_id'}
    for field in fields:
        setattr(doc1, field, getattr(doc2, field))


class ReduceMixin:
    """
    A mixin that provides reducing logic for :class:`DocumentArray` or :class:`DocumentArrayMemmap`
    Reducing 2 or more DocumentArrays consists in merging all Documents into the same DocumentArray.
    If a Document belongs to 2 or more DocumentArrays, it is added once and data attributes are merged with priority to
    the Document belonging to the left-most DocumentArray. Matches and chunks are also reduced in the same way.
    Reduction is applied to all levels of DocumentArrays, that is, from root Documents to all their chunk and match
    children.
    """

    def reduce(self: 'T', other: 'T') -> 'T':
        """
        Reduces other and the current DocumentArray into one DocumentArray in-place. Changes are applied to the current
        DocumentArray.
        Reducing 2 DocumentArrays consists in adding Documents in the second DocumentArray to the first DocumentArray
        if they do not exist. If a Document exists in both DocumentArrays, the data properties are merged with priority
        to the first Document (that is, to the current DocumentArray's Document). The matches and chunks are also
        reduced in the same way.
        :param other: DocumentArray
        :return: DocumentArray
        """
        for doc in other:
            if doc.id in self:
                self._reduce_doc(self[doc.id], doc)
            else:
                self.append(doc)

        return self

    @staticmethod
    def _reduce_doc(doc1: 'Document', doc2: 'Document'):
        """
        Reduces doc1 and doc2 into one Document in-place. Changes are applied to doc1.
        Reducing 2 Documents consists in setting data properties of the second Document to the first Document if they
        are empty (that is, priority to the left-most Document) and reducing the matches and the chunks of both
        documents.
        Non-data properties are ignored.
        Reduction of matches and chunks relies on :class:`DocumentArray`.:method:`reduce`.
        :param doc1: first Document
        :param doc2: second Document
        """
        _reduce_doc_props(doc1, doc2)
        if len(doc2.matches) > 0:
            doc1.matches.reduce(doc2.matches)

        if len(doc2.chunks) > 0:
            doc1.chunks.reduce(doc2.chunks)

    def reduce_all(self: 'T', others: List['T']) -> 'T':
        """
        Reduces a list of DocumentArrays and this DocumentArray into one DocumentArray. Changes are applied to this
        DocumentArray in-place.

        Reduction consists in reducing this DocumentArray with every DocumentArray in `others` sequentially using
        :class:`DocumentArray`.:method:`reduce`.
        The resulting DocumentArray contains Documents of all DocumentArrays.
        If a Document exists in many DocumentArrays, data properties are merged with priority to the left-most
        DocumentArrays (that is, if a data attribute is set in a Document belonging to many DocumentArrays, the
        attribute value of the left-most DocumentArray is kept).
        Matches and chunks of a Document belonging to many DocumentArrays are also reduced in the same way.
        Other non-data properties are ignored.

        .. note::
            - Matches are not kept in a sorted order when they are reduced. You might want to re-sort them in a later
                step.
            - The final result depends on the order of DocumentArrays when applying reduction.

        :param others: List of DocumentArrays to be reduced
        :return: the resulting DocumentArray
        """
        for da in others:
            self.reduce(da)
        return self
