from typing import Optional

from .document_set import DocumentSet

from google.protobuf.pyext._message import RepeatedCompositeContainer

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
        from ..document import Document
        if isinstance(self._docs_proto, RepeatedCompositeContainer):
            m = self._docs_proto.add()
            if document:
                m.CopyFrom(document.as_pb_object)
            match = Document(m)
        else:
            match = Document()
            if document:
                match.CopyFrom(document)
            self._docs_proto.append(match.as_pb_object)

        match.set_attrs(parent_id=self._ref_doc.id,
                        granularity=self._ref_doc.granularity + 1,
                        **kwargs)
        if not match.mime_type:
            match.mime_type = self._ref_doc.mime_type

        return match
