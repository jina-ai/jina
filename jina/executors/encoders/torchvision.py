__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from .. import BaseTorchExecutor
from ..decorators import batching, as_ndarray


class TorchEncoder(BaseTorchExecutor):
    def __init__(self,
                 model_name: str,
                 channel_axis: int = 1,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.channel_axis = channel_axis
        self._default_channel_axis = 1

    def build_model(self):
        self._build_model()

    def set_device(self):
        self.model.to(self._device)

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        if self.channel_axis != self._default_channel_axis:
            data = np.moveaxis(data, self.channel_axis, self._default_channel_axis)
        import torch
        _input = torch.from_numpy(data.astype('float32'))
        if self.on_gpu:
            _input = _input.cuda()
        _feature = self._get_features(_input).detach()
        if self.on_gpu:
            _feature = _feature.cpu()
        _feature = _feature.numpy()
        return self._get_pooling(_feature)

    def _build_model(self):
        raise NotImplementedError

    def _get_features(self, data):
        raise NotImplementedError

    def _get_pooling(self, feature_map):
        return feature_map
