__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


import numpy as np
from typing import Dict
from jina.executors.decorators import batching, as_ndarray
from ... import BaseExecutor


class BaseMultiModalEncoder(BaseExecutor):
    """
    :class:`BaseMultiModalEncoder` encodes data from multiple inputs (``text``, ``buffer``, ``blob`` or other ``embeddings``)
    into a single ``embedding``
    """

    def __init__(self,
                 field_by_modality: Dict[str, str] = {},
                 position_by_modality: Dict[str, str] = {},
                 *args,
                 **kwargs):
        """
        :param field_by_modality: the map of fields that should be extracted by modality
        :return:
        """
        super().__init__(*args, **kwargs)
        self.field_by_modality = field_by_modality
        self.position_by_modality = position_by_modality

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """
        :param data: a `B x ([M] x D)` numpy ``ndarray``, `B` is the size of the batch, `M` is the number of modalities
        :return: a `B x D` numpy ``ndarray``
        """
        raise NotImplementedError
