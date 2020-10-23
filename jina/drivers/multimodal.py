__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from collections import defaultdict
from typing import Iterable, Tuple

from .encode import BaseEncodeDriver
from .helper import pb2array, array2pb
from ..proto import jina_pb2


def _extract_doc_content(doc: 'jina_pb2.Document', field: str):
    if field in ['blob', 'embedding']:
        return pb2array(getattr(doc, field))
    elif field:
        return getattr(doc, field)


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
    def field_by_modality(self):
        if not getattr(self._exec, 'field_by_modality', None):
            raise RuntimeError('Could not know which fields to load for each modality')
        return self._exec.field_by_modality

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
        data = []
        for doc in docs:
            data_by_modality = defaultdict(list)

            for chunk in doc.chunks:
                # Group chunks which has the same modality
                # TODO: How should the driver know what does it need to extract per modality?
                data_by_modality[chunk.modality].append(_extract_doc_content(self.field_by_modality[chunk.modality]))
            data.append(data_by_modality)

        for doc, modality_dict in zip(docs, data):
            ret = self.exec_fn(modality_dict)
            doc.embeedding.CopyFrom(array2pb(ret))
