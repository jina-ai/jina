__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from collections import defaultdict
from typing import Tuple, Dict, List

import numpy as np

from .encode import BaseEncodeDriver
from ..types.document.multimodal import MultimodalDocument

if False:
    from ..types.sets import DocumentSet


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
            docs: 'DocumentSet',
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
            # convert to MultimodalDocument
            doc = MultimodalDocument(doc)
            if doc.modality_content_map:
                valid_docs.append(doc)
                for modality in self.positional_modality:
                    content_by_modality[modality].append(doc[modality])
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
                    f'mismatched {len(valid_docs)} docs from level {valid_docs[0].granularity} '
                    f'and a {embeds.shape} shape embedding, the first dimension must be the same')
            for doc, embedding in zip(valid_docs, embeds):
                doc.embedding = embedding
