from .document import DocumentSet

if False:
    from ..document import Document


class MatchSet(DocumentSet):
    def __init__(self, docs_proto, reference_doc: 'Document'):
        super().__init__(docs_proto)
        self._ref_doc = reference_doc

    def append(self, document: 'Document', **kwargs) -> 'Document':
        """Add a matched document to the current Document

        :return: the newly added sub-document in :class:`Document` view
        """
        from ..document import Document
        m = self._docs_proto.add()
        m.CopyFrom(document.proto)
        match = Document(m)

        match.set_attrs(granularity=self.granularity, adjacency=self.adjacency, **kwargs)
        match.score.ref_id = self._ref_doc.id

        if not match.mime_type:
            match.mime_type = self._ref_doc.mime_type

        return match

    @property
    def reference_doc(self) -> 'Document':
        """Get the document that this :class:`MatchSet` referring to"""
        return self._ref_doc

    @property
    def granularity(self) -> int:
        """The granularity of all document in this set """
        return self._ref_doc.granularity

    @property
    def adjacency(self) -> int:
        """The adjacency of all document in this set """
        return self._ref_doc.adjacency + 1