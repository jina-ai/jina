from typing import Optional

from .document_set import DocumentSet

if False:
    from ..document import Document


class MatchSet(DocumentSet):
    def __init__(self, docs_proto, reference_doc: 'Document'):
        super().__init__(docs_proto)
        self._ref_doc = reference_doc

    def append(self, document: Optional['Document'] = None, **kwargs) -> 'Document':
        """Add a matched document to the current Document

        :return: the newly added sub-document in :class:`Document` view
        """
        c = self._docs_proto.add()
        if document is not None:
            c.CopyFrom(document.as_pb_object)

        from ..document import Document
        m = Document(c)
        m.set_attrs(granularity=self._ref_doc.granularity,
                    adjacency=self._ref_doc.adjacency + 1,
                    **kwargs)

        m.score.ref_id = self._ref_doc.id
        if not m.mime_type:
            m.mime_type = self._ref_doc.mime_type
        return m
