__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from collections import defaultdict
from typing import Sequence, Tuple, Dict, List

import numpy as np

from .encode import BaseEncodeDriver
from ..proto import jina_pb2
from jina.types.ndarray.generic import NdArray


def _extract_doc_content(doc: 'jina_pb2.DocumentProto'):
    """Returns the content of the document with the following priority:
    If the document has an embedding, return it, otherwise return its content.
    """
    r = NdArray(doc.embedding).value
    if r is not None:
        return r
    elif doc.text or doc.buffer:
        return doc.text or doc.buffer
    else:
        return NdArray(doc.blob).value


def _extract_modalities_from_document(doc: 'jina_pb2.DocumentProto'):
    """Returns a dictionary of document content (embedding, text, blob or buffer) with `modality` as its key
    """
    doc_content = {}
    for chunk in doc.chunks:
        modality = chunk.modality
        if modality in doc_content:
            return None
        else:
            doc_content[modality] = _extract_doc_content(chunk)
    return doc_content


class MultiModalDriver(BaseEncodeDriver):
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
    .. warning::
        - It assumes that every ``chunk`` of a ``document`` belongs to a different modality.
    """

    def __init__(self,
                 traversal_paths: Tuple[str] = ('r',), *args, **kwargs):
        super().__init__(traversal_paths=traversal_paths, *args, **kwargs)

    @property
    def positional_modality(self) -> List[str]:
        """Get position per modality.
        :return: the list of strings representing the name and order of the modality.
        """
        if not self._exec.positional_modality:
            raise RuntimeError('Could not know which position of the ndarray to load to each modality')
        return self._exec.positional_modality

    def _get_executor_input_arguments(self, content_by_modality: Dict[str, 'np.ndarray']):
        """
            From a dictionary ``content_by_modality`` it returns the arguments in the proper order so that they can be
            passed to the executor.
        """
        return [content_by_modality[modality] for modality in self.positional_modality]

    def _apply_all(
            self,
            docs: Sequence['jina_pb2.DocumentProto'],
            *args, **kwargs
    ) -> None:
        """
        :param docs: the docs for which a ``multimodal embedding`` will be computed, whose chunks are of different
        modalities
        :return:
        """
        content_by_modality = defaultdict(list)  # array of num_rows equal to num_docs and num_columns equal to

        valid_docs = []
        for doc in docs:
            doc_content = _extract_modalities_from_document(doc)
            if doc_content:
                valid_docs.append(doc)
                for modality in self.positional_modality:
                    content_by_modality[modality].append(doc_content[modality])
            else:
                self.logger.warning(f'Invalid doc {doc.id}. Only one chunk per modality is accepted')

        if len(valid_docs) > 0:
            # Pass a variable length argument (one argument per array)
            for modality in self.positional_modality:
                content_by_modality[modality] = np.stack(content_by_modality[modality])

            # Guarantee that the arguments are provided to the executor in its desired order
            input_args = self._get_executor_input_arguments(content_by_modality)
            embeds = self.exec_fn(*input_args)
            if len(valid_docs) != embeds.shape[0]:
                self.logger.error(
                    f'mismatched {len(valid_docs)} docs from level {docs[0].granularity} '
                    f'and a {embeds.shape} shape embedding, the first dimension must be the same')
            for doc, embedding in zip(valid_docs, embeds):
                NdArray(doc.embedding).value = embedding
