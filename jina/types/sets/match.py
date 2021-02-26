from .document import DocumentSet

if False:
    from ..document import Document


class MatchSet(DocumentSet):
    """
    :class:`MatchSet` inherits from :class:`DocumentSet`.
    It's a subset of Documents that represents the matches

    :param docs_proto: Set of matches of the `reference_doc`
    :type docs_proto: :class:`Document`
    :param reference_doc: Reference :class:`Document` for the sub-documents
    :type reference_doc: :class:`Document`
    """

    def __init__(self, docs_proto, reference_doc: 'Document'):
        super().__init__(docs_proto)
        self._ref_doc = reference_doc

    def append(self, document: 'Document', **kwargs) -> 'Document':
        """Add a matched document to the current Document.

        :param document: Sub-document to be added
        :type document: :class: `Document
        :param kwargs: Extra key value arguments
        :return: the newly added sub-document in :class:`Document` view
        :rtype: :class:`Document` view
        """
        from ..document import Document
        m = self._docs_proto.add()
        m.CopyFrom(document.proto)
        match = Document(m)

        match.set_attrs(granularity=self.granularity, adjacency=self.adjacency, **kwargs)
        match.score.ref_id = self._ref_doc.id

        return match

    @property
    def reference_doc(self) -> 'Document':
        """Get the document that this :class:`MatchSet` referring to.
        :return: the document the match refers to
        """
        return self._ref_doc

    @property
    def granularity(self) -> int:
        """Get granularity of all document in this set.
        :return: the granularity of the documents of which these are match
        """
        return self._ref_doc.granularity

    @property
    def adjacency(self) -> int:
        """Get the adjacency of all document in this set.
        :return: the adjacency of the set of matches
        """
        return self._ref_doc.adjacency + 1
