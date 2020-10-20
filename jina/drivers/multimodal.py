__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable

from . import BaseRecursiveDriver
from .helper import pb2array

class MultimodalDriver(BaseRecursiveDriver):
    """
    TODO add docstring
    each document have multiple chunks
    each chunk has 1 modality
    group chunk i
    """
    def __init__(self, traversal_paths=('c', ), *args, **kwargs):
        # traversal chunks from chunk level.
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def _apply_all(
            self,
            docs: Iterable['jina_pb2.Document'],
            context_doc: 'jina_pb2.Document',
            field: str,
            *args,
            **kwargs
    ) -> None:
        """"""
        # extract all the required fields from the chunks of a document (buffer, blob, text,
        # or directly embedding)
        for doc in docs:
            doc_instance = {}
            doc_instance['id'] = doc.id
            chunks = doc.chunks
            for chunk in chunks:
                modality = chunk.modality
                doc_instance[modality] = {}
                doc_instance[modality][chunk.id]['content'] = self._extract_content(chunk)
                doc_instance[modality][chunk.id]['embedding'] = self._extract_embedding(chunk)
            # Set the return value to the context_doc embedding.


    def _extract_content(self, chunk):
        return chunk.text or chunk.buffer or (chunk.blob and pb2array(chunk.blob))

    def _extract_embedding(self, chunk):
        return (chunk.embedding.buffer or None) and pb2array(chunk.embedding)



