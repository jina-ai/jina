__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
import re

import numpy as np

from ...decorators import batching, as_ndarray
from ... import BaseOnnxExecutor


class OnnxImageEncoder(BaseOnnxExecutor):
    """
    :class:`OnnxImageEncoder` encodes data from a ndarray, potentially B x (Channel x Height x Width) into a
        ndarray of `B x D`.
    Internally, :class:`OnnxImageEncoder` wraps the models from `onnxruntime`.
    """

    def __init__(self,
                 pool_strategy: str = 'mean',
                 *args, **kwargs):
        """

        :param pool_strategy: the pooling strategy
            - `None` means that the output of the model will be the 4D tensor output of the last convolutional block.
            - `mean` means that global average pooling will be applied to the output of the last convolutional block,
            and thus the output of the model will be a 2D tensor.
            - `max` means that global max pooling will be applied.
        """
        super().__init__(*args, **kwargs)
        self.pool_strategy = pool_strategy
        if pool_strategy not in ('mean', 'max', None):
            raise NotImplementedError('unknown pool_strategy: {}'.format(self.pool_strategy))

    def post_init(self):
        """
        Load the model from the `.onnx` file and add outputs for the selected layer, i.e. ``outputs_name``. The modified
             models is saved at `tmp_model_path`.
        """
        self._init_model()
        self.inputs_name = self.model.get_inputs()[0].name

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a `B x (Channel x Height x Width)` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``, `D` is the output dimension
        """
        results = []
        for idx in range(data.shape[0]):
            img = np.expand_dims(data[idx, :, :, :], axis=0).astype('float32')
            data_encoded, *_ = self.model.run([self.outputs_name, ], {self.inputs_name: img})
            results.append(data_encoded)
        feature_map = np.concatenate(results, axis=0)
        if feature_map.ndim == 2 or self.pool_strategy is None:
            return feature_map
        return getattr(np, self.pool_strategy)(feature_map, axis=(2, 3))
