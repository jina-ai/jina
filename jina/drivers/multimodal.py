__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from collections import defaultdict
from typing import Iterable, Tuple

from .encode import BaseEncodeDriver
from .helper import pb2array, array2pb
from ..proto import jina_pb2


def _extract_doc_content(doc: 'jina_pb2.Document'):
    # TODO discuss when do we need doc content as described in the requirement
    # designing a driver that will extract all the required fields from the chunks of a document
    # (buffer, blob, text, or directly embedding)
    return doc.text or doc.buffer or (doc.blob and pb2array(doc.blob))


def _extract_doc_embedding(doc: 'jina_pb2.Document'):
    return (doc.embedding.buffer or None) and pb2array(doc.embedding)


class MultimodalDriver(BaseEncodeDriver):
    """
    TODO add docstring
    each document have multiple chunks
    each chunk has 1 modality
    group chunks with same modality
    """

    def __init__(self, traversal_paths: Tuple[str] = ('r',), *args, **kwargs):
        # traversal chunks from chunk level.
        # TODO discuss should we add root path
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    def _apply_all(
            self,
            docs: Iterable['jina_pb2.Document'],
            context_doc: 'jina_pb2.Document',
            *args, **kwargs
    ) -> None:
        # docs are documents whose chunks are multimodal
        # This is similar to ranking, needed to have batching?
        data = []
        for doc in docs:
            data_by_modality = defaultdict(list)
            for chunk in doc.chunks:
                # Group chunks which has the same modality
                # TODO: How should the driver know what does it need to extract per modality?
                data_by_modality[chunk.modality].append(_extract_doc_embedding(chunk))
            data.append(data_by_modality)

        for doc, modality_dict in zip(docs, data):
            ret = self.exec_fn(modality_dict)
            doc.embeedding.CopyFrom(array2pb(ret))
