from .document_set import DocumentSet

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
        m.CopyFrom(document.as_pb_object)
        match = Document(m)

        match.set_attrs(granularity=self._ref_doc.granularity,
                        adjacency=self._ref_doc.adjacency + 1,
                        **kwargs)
        match.score.ref_id = self._ref_doc.id

        if not match.mime_type:
            match.mime_type = self._ref_doc.mime_type

        return match
