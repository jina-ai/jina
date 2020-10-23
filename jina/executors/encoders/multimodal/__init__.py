__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


import numpy as np
from typing import Dict, Any
from jina.executors.decorators import batching, as_ndarray
from ... import BaseExecutor


class BaseMultiModalEncoder(BaseExecutor):
    """
    :class:`BaseMultiModalEncoder` encodes data from multiple inputs (``text``, ``buffer``, ``blob`` or other ``embeddings``)
    into a single ``embedding``
    """

    def __init__(self,
                 field_by_modality: Dict[str, str] = {},
                 *args,
                 **kwargs):
        """
        :param field_by_modality: the map of fields that should be extracted by modality
        :return:
        """
        super().__init__(*args, **kwargs)
        self.field_by_modality = field_by_modality

    @batching
    @as_ndarray
    def encode(self, data: Dict[str, Any], *args, **kwargs) -> 'np.ndarray':
        raise NotImplementedError
