from typing import Dict, List, TypeVar

import numpy as np

from . import Document
from ...proto import jina_pb2
from ..ndarray.generic import NdArray
from ...excepts import LengthMismatchException, BadDocType

__all__ = ['MultimodalDocument', 'DocumentContentType']

DocumentContentType = TypeVar('DocumentContentType', bytes, str,
                              np.ndarray, jina_pb2.NdArrayProto, NdArray)

class MultimodalDocument(Document):
    """Each :class:`MultimodalDocument` should have at least 2 chunks (represent as :class:`ChunkSet`)
    and len(set(doc.chunks.modality)) == len(doc.chunks)
    """
    def __init__(self, document = None, copy: bool = False, **kwargs):
        super().__init__(document=document, copy=copy, **kwargs)
        self._modality_content_mapping = {}

    def _build_modality_content_mapping(self) -> Dict:
        for chunk in self.chunks:
            modality = chunk.modality
            self._modality_content_mapping[modality] = chunk.embedding \
                if chunk.embedding is not None \
                else chunk.content
        self._validate()

    def _validate(self):
        if len(self.chunks) < 2:
            raise BadDocType('MultimodalDocument should consist at least 2 chunks.')
        if len(self._modality_content_mapping.keys()) != len(self.chunks):
            raise LengthMismatchException(f'Length of modality is not identical to length of chunks.')

    @property
    def modality_content_mapping(self):
        if not self._modality_content_mapping:
            self._build_modality_content_mapping()
        return self._modality_content_mapping

    def extract_content_by_modality(self, modality: str):
        return self.modality_content_mapping.get(modality, None)

    @property
    def modalities(self) -> List[str]:
        return self.modality_content_mapping.keys()
