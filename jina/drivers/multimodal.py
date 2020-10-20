__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Iterable, Dict

import numpy as np

from .reduce import ReduceDriver
from .helper import pb2array, array2pb

class MultimodalDriver(ReduceDriver):
    """
    TODO add docstring
    each document have multiple chunks
    each chunk has 1 modality
    group chunk i
    """
    def __init__(self, traversal_paths=('c', ), *args, **kwargs):
        # traversal chunks from chunk level.
        # TODO discuss should we add root path
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def reduce(self, *args, **kwargs) -> None:
        doc_pointers = {}
        # traverse apply on ALL requests collected to collect embeddings
        # reversed since the last response should collect the chunks/matches
        for r in reversed(self.prev_reqs):
            self._traverse_apply(r.docs, doc_pointers=doc_pointers, *args, **kwargs)

        self._traverse_apply(
            self.req.docs,
            doc_pointers=doc_pointers,
            concatenate_by_modality=True,
            *args, **kwargs
        )

    def _apply_all(
            self,
            docs: Iterable['jina_pb2.Document'],
            context_doc: 'jina_pb2.Document',
            field: str,
            doc_pointers: Dict,
            concatenate_by_modality: bool = False,
            *args,
            **kwargs
    ) -> None:
        # docs are chunks of context_doc returned by traversal rec.
        # Group chunks which has the same modality
        modal_doc = {}
        for doc in docs:
            modal = doc.modality
            if doc.id in modal_doc:
                modal_doc[modal].append(doc.id)
            else:
                modal_doc[modal] = [doc.id]

        for modal, doc_ids in modal_doc.items():
            if concatenate_by_modality:
                embeddings_with_same_modality = [
                    doc_pointers[doc_id]
                    for
                    doc_id
                    in
                    doc_ids
                ]
                context_doc.embedding.CopyFrom(
                    array2pb(
                        np.concatenate(
                            embeddings_with_same_modality,
                            axis=0)
                    )
                )
            else:
                embedding = self._extract_chunk_level_embedding(doc)
                if doc.id not in doc_pointers:
                    doc_pointers[doc.id] = [embedding]
                else:
                    doc_pointers[doc.id].append(embedding)


    def _extract_doc_content(self, doc):
        # TODO discuss when do we need doc content as described in the requirement
        # designing a driver that will extract all the required fields from the chunks of a document
        # (buffer, blob, text, or directly embedding)
        return  doc.text or doc.buffer or (doc.blob and pb2array(doc.blob))


    def _extract_doc_embedding(self, doc):
        return (doc.embedding.buffer or None) and pb2array(doc.embedding)
