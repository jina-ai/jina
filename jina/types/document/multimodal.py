from typing import List

from . import Document
from ...excepts import LengthMismatchException, BadDocType

class MultimodalDocument(Document):
    """Each :class:`MultimodalDocument` should have at least 2 chunks (represent as :class:`DocumentSet`)
    and len(set(doc.chunks.modality)) == len(doc.chunk)
    """
    def __init__(self, document = None,
                 copy: bool = False, **kwargs):
        super().__init__(document=document, copy=copy, **kwargs)
        self._modalities = set()
        if len(self._document.chunks) < 2:
            raise BadDocType(
                f'A MultimodalDocument should have at least 2 modalities, {len(self.document.chunks)} received.')
        if len(self._document.chunks) != len(self.modalities):
            raise LengthMismatchException(
                f'Document has {len(self._document.chunks)} chunks and {len(self.modalities)} modalities')

    def extract_modalities(self) -> List[str]:
        doc_content = {}
        for chunk in self._document.chunks:
            modality = chunk.modality
            if modality in self._modality_by_chunk:
                continue
            else:
                doc_content[modality] = chunk.embedding \
                    if chunk.embedding is not None \
                    else chunk.content
        return doc_content

    @property
    def modalities(self) -> List[str]:
        # TODO Decide do we need to preserve the order
        if not self._modalities:
            for chunk in self._document.chunks():
                self._modalities.add(chunk.modality)
        return list(self._modalities)
