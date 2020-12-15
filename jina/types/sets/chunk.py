from .document import DocumentSet

if False:
    from ..document import Document


class ChunkSet(DocumentSet):
    def __init__(self, docs_proto, reference_doc: 'Document'):
        super().__init__(docs_proto)
        self._ref_doc = reference_doc

    def append(self, document: 'Document', **kwargs) -> 'Document':
        """Add a sub-document (i.e chunk) to the current Document

        :return: the newly added sub-document in :class:`Document` view

        .. note::
            Comparing to :attr:`DocumentSet.append()`, this method adds more safeguard to
            make sure the added chunk is legit.
        """

        from ..document import Document
        c = self._docs_proto.add()
        c.CopyFrom(document.as_pb_object)
        chunk = Document(c)

        chunk.set_attrs(parent_id=self._ref_doc.id,
                        granularity=self.granularity,
                        **kwargs)

        if not chunk.mime_type:
            chunk.mime_type = self._ref_doc.mime_type
        chunk.update_content_hash()
        return chunk

    @property
    def parent_doc(self) -> 'Document':
        """Get the document that this :class:`ChunkSet` belonging to"""
        return self._ref_doc

    @property
    def granularity(self) -> int:
        """The granularity of all document in this set """
        return self._ref_doc.granularity + 1

    @property
    def adjacency(self) -> int:
        """The adjacency of all document in this set """
        return self._ref_doc.adjacency
