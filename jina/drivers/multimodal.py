__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np
from collections import defaultdict
from typing import Iterable, Tuple

from .encode import BaseEncodeDriver
from .helper import pb2array, array2pb
from ..proto import jina_pb2


def _extract_doc_content(doc: 'jina_pb2.Document'):
    if doc.embedding:
        return pb2array(doc.embedding)
    else:
        return doc.text or doc.buffer or (doc.blob and pb2array(doc.blob))


class MultimodalDriver(BaseEncodeDriver):
    """Extract multimodal embeddings from different modalities.
    Input-Output ::
        Input:
        document:
                |- chunk: {modality: mode1}
                |
                |- chunk: {modality: mode2}
        Output:
        document: (embedding: multimodal encoding)
                |- chunk: {modality: mode1}
                |
                |- chunk: {modality: mode2}

    .. note::
        - It traverses on the ``documents`` for which we want to apply the ``multimodal`` embedding. This way
        we can use the `batching` capabilities for the `executor`.
        - It assumes that every ``chunk`` of a ``document`` belongs to a different modality.
    """

    def __init__(self,
                 traversal_paths: Tuple[str] = ('r',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    @property
    def position_by_modality(self):
        if not getattr(self._exec, 'position_by_modality', None):
            raise RuntimeError('Could not know which position of the ndarray to load to each modality')
        return self._exec.position_by_modality

    def _apply_all(
            self,
            docs: Iterable['jina_pb2.Document'],
            *args, **kwargs
    ) -> None:
        """
        :param docs: the docs for which a ``multimodal embedding`` will be computed
        :return:
        """
        # docs are documents whose chunks are multimodal
        # This is similar to ranking, needed to have batching?
        num_modalities = len(self.position_by_modality.keys())
        content_by_modality = defaultdict(list)  # array of num_rows equal to num_docs and num_columns equal to

        # num_modalities
        valid_docs = []
        for doc in docs:
            doc_content = [None] * num_modalities
            valid = True
            for chunk in doc.chunks:
                modality_idx = self.position_by_modality[chunk.modality]
                if doc_content[modality_idx]:
                    valid = False
                    self.logger.warning(f'Invalid doc {doc.id}. Only one chunk per modality is accepted')
                else:
                    doc_content[modality_idx] = _extract_doc_content(chunk)
            if valid:
                valid_docs.append(doc)
                for idx in range(num_modalities):
                    content_by_modality[idx].append(doc_content[idx])

        if len(valid_docs) > 0:
            # I want to pass a variable length argument (one argument per array)
            for _ in range(num_modalities):
                content_by_modality[_] = np.stack(content_by_modality[_], axis=0)
            embeds = self.exec_fn(*content_by_modality.values())
            if len(valid_docs) != embeds.shape[0]:
                self.logger.error(
                    f'mismatched {len(valid_docs)} docs from level {docs[0].granularity} '
                    f'and a {embeds.shape} shape embedding, the first dimension must be the same')
            for doc, embedding in zip(valid_docs, embeds):
                doc.embedding.CopyFrom(array2pb(embedding))
