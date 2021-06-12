from .document import DocumentArray

if False:
    from ..document import Document


class MatchArray(DocumentArray):
    """
    :class:`MatchArray` inherits from :class:`DocumentArray`.
    It's a subset of Documents that represents the matches

    :param doc_views: Set of matches of the `reference_doc`
    :param reference_doc: Reference :class:`Document` for the sub-documents
    """

    def __init__(self, doc_views, reference_doc: 'Document'):
        self._ref_doc = reference_doc
        super().__init__(doc_views)

    def append(self, document: 'Document', **kwargs) -> 'Document':
        """Add a matched document to the current Document.

        :param document: Sub-document to be added
        :type document: :class: `Document
        :param kwargs: Extra key value arguments
        :return: the newly added sub-document in :class:`Document` view
        :rtype: :class:`Document` view
        """
        from ..document import Document

        match = Document(document, copy=True)

        match.set_attributes(
            granularity=self.granularity, adjacency=self.adjacency, **kwargs
        )
        match.score.ref_id = self._ref_doc.id

        super().append(match)
        return match

    @property
    def reference_doc(self) -> 'Document':
        """Get the document that this :class:`MatchArray` referring to.
        :return: the document the match refers to
        """
        return self._ref_doc

    @property
    def granularity(self) -> int:
        """Get granularity of all document in this array.
        :return: the granularity of the documents of which these are match
        """
        return self._ref_doc.granularity

    @property
    def adjacency(self) -> int:
        """Get the adjacency of all document in this array.
        :return: the adjacency of the array of matches
        """
        return self._ref_doc.adjacency + 1
