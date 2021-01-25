from typing import Dict, Sequence, List, Optional, Any, Tuple

from . import Document, DocumentSourceType, typename, DocumentContentType
from ...excepts import BadDocType

__all__ = ['MultimodalDocument']


class MultimodalDocument(Document):
    """
    :class:`MultimodalDocument` is a data type created based on Jina primitive data type :class:`Document`.

    It shares the same methods and properties with :class:`Document`, while it focus on modality at chunk level.

    .. warning::
        - It assumes that every ``chunk`` of a ``document`` belongs to a different modality.
        - It assumes that every :class:`MultimodalDocument` have at least two chunks.
    """

    def __init__(self, document: Optional[DocumentSourceType] = None,
                 chunks: Sequence[Document] = None,
                 modality_content_map: Dict[str, DocumentContentType] = None,
                 copy: bool = False, **kwargs):
        """

        :param document: the document to construct from. If ``bytes`` is given
                then deserialize a :class:`DocumentProto`; ``dict`` is given then
                parse a :class:`DocumentProto` from it; ``str`` is given, then consider
                it as a JSON string and parse a :class:`DocumentProto` from it; finally,
                one can also give `DocumentProto` directly, then depending on the ``copy``,
                it builds a view or a copy from it.
        :param chunks: the chunks of the multimodal document to initialize with. Expected to
                received a list of :class:`Document`, with different modalities.
        :param: `modality_content_mapping`: A Python dict, the keys are the modalities and the values
                are the :attr:`content` of the :class:`Document`
        :param copy: when ``document`` is given as a :class:`DocumentProto` object, build a
                view (i.e. weak reference) from it or a deep copy from it.
        :param kwargs: other parameters to be set

        .. warning::
            - Build :class:`MultimodalDocument` from :attr:`modality_content_mapping` expects you assign
              :attr:`Document.content` as the value of the dictionary.
        """
        super().__init__(document=document, copy=copy, **kwargs)
        if chunks or modality_content_map:
            if chunks:
                granularities = [chunk.granularity for chunk in chunks]
                if len(set(granularities)) != 1:
                    raise BadDocType('Each chunk should have the same granularity.')
                self.chunks.extend(chunks)
            elif modality_content_map:
                self.modality_content_map = modality_content_map
            self._handle_chunk_level_attributes()

    @property
    def is_valid(self) -> bool:
        """A valid :class:`MultimodalDocument` should meet the following requirements:

            - Document should consist at least 2 chunks.
            - Length of modality is not identical to length of chunks.
        """
        modalities = set([chunk.modality for chunk in self.chunks])
        return 2 <= len(self.chunks) == len(modalities)

    def _handle_chunk_level_attributes(self):
        """Handle chunk attributes, such as :attr:`granularity` and :attr:`mime_type`.

        Chunk granularity should be greater than parent granularity level. Besides, if the chunk do not have
            a specified :attr:`mime_type`, it will be manually set to it's parent's :attr:`mime_type`.
        """

        # Joan: https://github.com/jina-ai/jina/pull/1335#discussion_r533905780
        # If chunk.granularity is 0. (This means a user without caring for granularity wants
        #   to merge N documents into a multimodal document, therefore we do what
        #   u have here of increasing their granularity inside this set) Well documented please
        # If the chunk comes with granularity > 0, then it means that someone has cared to chunk already
        #   the document or that we have some driver that generates muktimodal documents in the future.
        #   Then, have document.granularity = chunk.granularity - 1.
        for chunk in self.chunks:
            if chunk.granularity == 0:
                chunk.granularity = self.granularity + 1
            else:
                self.granularity = chunk.granularity - 1
            if not chunk.mime_type:
                chunk.mime_type = self.mime_type

    @property
    def modality_content_map(self) -> Dict:
        """Get the mapping of modality and content, the mapping is represented as a :attr:`dict`, the keys
        are the modalities of the chunks, the values are the corresponded content of the chunks.

        :return: the mapping of modality and content extracted from chunks.
        """
        result = {}
        for chunk in self.chunks:
            modality = chunk.modality
            result[modality] = chunk.embedding if chunk.embedding is not None else chunk.content
        return result

    @modality_content_map.setter
    def modality_content_map(self, value: Dict[str, Any]):
        for modality, content in value.items():
            with Document() as chunk:
                chunk.modality = modality
                chunk.content = content
                self.chunks.add(chunk)

    def __getitem__(self, modality: str) -> DocumentContentType:
        """Extract content by the name of the modality.

        :param modality: The name of the modality.
        :return: Content of the corresponded modality.
        """
        if isinstance(modality, str):
            return self.modality_content_map.get(modality, None)
        else:
            raise TypeError(f'{typename(modality)} is not supported')

    @property
    def modalities(self) -> List[str]:
        """Get all modalities of the :class:`MultimodalDocument`.

        :return: List of modalities extracted from chunks of the document.
        """
        return list(self.modality_content_map.keys())

    def update_content_hash(self, exclude_fields: Tuple[str] = ('id', 'matches', 'content_hash')) -> None:
        """ Update content hash of the document by including ``chunks`` when computing the hash
        """
        super().update_content_hash(exclude_fields)
