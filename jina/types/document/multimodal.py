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
    """
    :class:`MultimodalDocument` is a data type created based on Jina primitive data type :class:`Document`.

    It shares the same methods and properties with :class:`Document`, while it focus on modality at chunk level.

    .. warning::
        - It assumes that every ``chunk`` of a ``document`` belongs to a different modality.
        - It assumes that every :class:`MultimodalDocument` have at least two chunks.
    """
    def __init__(self, document = None, chunks: List[Document] = None, copy: bool = False, **kwargs):
        """

        :param document: the document to construct from. If ``bytes`` is given
                then deserialize a :class:`DocumentProto`; ``dict`` is given then
                parse a :class:`DocumentProto` from it; ``str`` is given, then consider
                it as a JSON string and parse a :class:`DocumentProto` from it; finally,
                one can also give `DocumentProto` directly, then depending on the ``copy``,
                it builds a view or a copy from it.
        :param chunks: the chunks of the multimodal document to initialize with. Expected to
                received a list of :class:`Document`, with different modalities.
        :param copy: when ``document`` is given as a :class:`DocumentProto` object, build a
                view (i.e. weak reference) from it or a deep copy from it.
        :param kwargs: other parameters to be set
        """
        super().__init__(document=document, copy=copy, **kwargs)
        self._modality_content_mapping = {}
        if chunks:
            self._validate(chunks)
            self.chunks.clear()
            self.chunks.extend(chunks)

    def _build_modality_content_mapping(self) -> Dict:
        for chunk in self.chunks:
            modality = chunk.modality
            self._modality_content_mapping[modality] = chunk.embedding \
                if chunk.embedding is not None \
                else chunk.content
        self._validate(chunks=self.chunks)

    def _validate(self, chunks: List[Document]):
        modalities = set([chunk.modality for chunk in chunks])
        if len(chunks) < 2:
            raise BadDocType('MultimodalDocument should consist at least 2 chunks.')
        if len(modalities) != len(chunks):
            raise LengthMismatchException(f'Length of modality is not identical to length of chunks.')

    @property
    def modality_content_mapping(self) -> Dict:
        """Get the mapping of modality and content, the mapping is represented as a :attr:`dict`, the keys
        are the modalities of the chunks, the values are the corresponded content of the chunks.

        :return: the mapping of modality and content extracted from chunks.
        """
        if not self._modality_content_mapping:
            self._build_modality_content_mapping()
        return self._modality_content_mapping

    def extract_content_by_modality(self, modality: str) -> DocumentContentType:
        """Extract content by the name of the modality.

        :param modality: The name of the modality.
        :return: Content of the corresponded modality.
        """
        return self.modality_content_mapping.get(modality, None)

    @property
    def modalities(self) -> List[str]:
        """Get all modalities of the :class:`MultimodalDocument`.

        :return: List of modalities extracted from chunks of the document.
        """
        return self.modality_content_mapping.keys()

    @classmethod
    def from_chunks(cls, chunks: List[Document]) -> 'MultimodalDocument':
        """Create :class:`MultimodalDocument` from a list of chunks.

        :param chunks: List of :class:`Document` to be added as chunks.
        :return: An instance of :class:`MultimodalDocument`.
        """
        return cls(chunks=chunks)
