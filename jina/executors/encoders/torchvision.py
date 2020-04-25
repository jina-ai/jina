__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from . import BaseNumericEncoder
from ..decorators import batching, as_ndarray


class TorchEncoder(BaseNumericEncoder):
    def __init__(self,
                 model_name: str,
                 channel_axis: int = 1,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.channel_axis = channel_axis
        self._default_channel_axis = 1

    def post_init(self):
        import torch
        self._build_model()
        device = 'cuda:0' if self.on_gpu else 'cpu'
        self.model.to(torch.device(device))

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        if self.channel_axis != self._default_channel_axis:
            data = np.moveaxis(data, self.channel_axis, self._default_channel_axis)
        import torch
        feature_map = self._get_features(torch.from_numpy(data.astype('float32'))).detach().numpy()
        return self._get_pooling(feature_map)

    def _build_model(self):
        raise NotImplementedError

    def _get_features(self, data):
        raise NotImplementedError

    def _get_pooling(self, feature_map):
        return feature_map
