from typing import Optional

from .document_set import DocumentSet

if False:
    from ..document import Document


class ChunkSet(DocumentSet):
    def __init__(self, docs_proto, reference_doc: 'Document'):
        super().__init__(docs_proto)
        self._ref_doc = reference_doc

    def append(self, document: Optional['Document'] = None, **kwargs) -> 'Document':
        """Add a sub-document (i.e chunk) to the current Document

        :return: the newly added sub-document in :class:`Document` view

        .. note::
            Comparing to :attr:`DocumentSet.append()`, this method adds more safeguard to
            make sure the added chunk is legit.
        """
        from ..document import Document
        with Document() as chunk:
            if document:
                chunk.CopyFrom(document)

            chunk.set_attrs(parent_id=self._ref_doc.id,
                            granularity=self._ref_doc.granularity + 1,
                            **kwargs)

            if not chunk.mime_type:
                chunk.mime_type = self._ref_doc.mime_type

            self._docs_proto.append(chunk.as_pb_object)
            return chunk
