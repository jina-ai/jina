from typing import List, TYPE_CHECKING


if TYPE_CHECKING:
    from ..document import DocumentArray
    from ...document import Document
    from ....helper import T


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
    """A mixing that provides reducing logic for :class:`DocumentArray` or :class:`DocumentArrayMemmap`"""

    def reduce(self: 'T', other: 'T') -> 'T':
        """
        Reduces other and the current DocumentArray into one DocumentArray in-place. Changes are applied to the current
        DocumentArray.
        Reducing 2 DocumentArrays consists in adding Documents in the second DocumentArray to the first DocumentArray
        if they do not exist. If a Document exists in both DocumentArrays, the data properties are merged with priority
        to the first Document (that is, to the current DocumentArray's Document). The matches and chunks are also
        reduced.
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
        are empty and reducing the matches and the chunks of both documents.
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

        Reduction consists in reducing this DocumentArray with every DocumentArray in others sequentially using
        :class:`DocumentArray`.:method:`reduce`.
        The resulting DocumentArray contains Documents of all DocumentArrays.
        If a Document exists in many DocumentArrays, data properties are merged with priority to the left-most
        DocumentArrays (that is, if a data attribute is set in a Document belonging to many DocumentArrays, the
        attribute value of the left-most DocumentArray is kept.
        Non-data properties are ignored.
        Matches and chunks of a Document belonging to many DocumentArrays are also reduced in the same way.

        .. note::
            - Matches are not kept in a sorted order when they are reduced. You might want to re-sort them in a later
                step.
            - The final result depends on the order of DocumentArrays when applying reduction.

        :param others: List of DocumentArray to be reduced
        :return: the resulting DocumentArray
        """
        for da in others:
            self.reduce(da)
        return self
