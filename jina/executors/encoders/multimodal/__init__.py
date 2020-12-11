__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Sequence

import numpy as np

from ... import BaseExecutor


class BaseMultiModalEncoder(BaseExecutor):
    """
    :class:`BaseMultiModalEncoder` encodes data from multiple inputs (``text``, ``buffer``, ``blob`` or other ``embeddings``)
    into a single ``embedding``
    """

    def __init__(self,
                 positional_modality: Sequence[str],
                 *args,
                 **kwargs):
        """
        :param positional_modality: the list of arguments indicating in which order the modalities they need to come
        for the encoding method
        :return:
        """
        super().__init__(*args, **kwargs)
        self.positional_modality = positional_modality

    def encode(self, *data: 'np.ndarray', **kwargs) -> 'np.ndarray':
        """
        :param: data: M arguments of shape `B x (D)` numpy ``ndarray``, `B` is the size of the batch, `M` is the number of modalities
        :return: a `B x D` numpy ``ndarray``
        """
        raise NotImplementedError
