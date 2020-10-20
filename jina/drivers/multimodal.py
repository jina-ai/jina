__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable, Dict

from .reduce import ReduceDriver
from .helper import pb2array

class MultimodalDriver(ReduceDriver):
    """
    TODO add docstring
    each document have multiple chunks
    each chunk has 1 modality
    group chunk i
    """
    def __init__(self, traversal_paths=('c', ), *args, **kwargs):
        # traversal chunks from chunk level.
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def reduce(self, *args, **kwargs) -> None:
        doc_pointers = {}
        # traverse apply on ALL requests collected to collect embeddings
        # reversed since the last response should collect the chunks/matches
        for r in reversed(self.prev_reqs):
            self._traverse_apply(r.docs, doc_pointers=doc_pointers, *args, **kwargs)

    def _apply_all(
            self,
            docs: Iterable['jina_pb2.Document'],
            context_doc: 'jina_pb2.Document',
            field: str,
            doc_pointers: Dict,
            *args,
            **kwargs
    ) -> None:
        # docs are chunks get by traversal rec
        for doc in docs:
            modality = doc.modality
            content = self._extract_chunk_level_content(doc) # one of buffer, blob or text.
            embedding = self._extract_chunk_level_embedding(doc) # directly embedding



    def _extract_chunk_level_content(self, doc):
        return doc.text or doc.buffer or (doc.blob and pb2array(doc.blob))

    def _extract_chunk_level_embedding(self, doc):
        return (doc.embedding.buffer or None) and pb2array(doc.embedding)



