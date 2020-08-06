__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from ..frameworks import BaseTorchEncoder, BasePaddleEncoder
from ...decorators import batching, as_ndarray


class BaseCVTorchEncoder(BaseTorchEncoder):
    """"
    :class:`BaseTorchEncoder` implements the common part for :class:`ImageTorchEncoder` and :class:`VideoTorchEncoder`.

    ..warning::
        :class:`BaseTorchEncoder`  is not intented to be used to do the real encoding.
    """

    def __init__(self, channel_axis: int = 1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_axis = channel_axis
        self._default_channel_axis = 1

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

    def _get_features(self, data):
        raise NotImplementedError

    def _get_pooling(self, feature_map):
        return feature_map


class BaseCVPaddleEncoder(BasePaddleEncoder):
    """
    :class:`BaseCVPaddleEncoder` implements the common parts for :class:`ImagePaddlehubEncoder` and
        :class:`VideoPaddleEncoder`.

    ..warning::
        :class:`BaseCVPaddleEncoder`  is not intented to be used to do the real encoding.
    """

    def __init__(self,
                 model_name: str,
                 output_feature: str = None,
                 pool_strategy: str = None,
                 channel_axis: int = -3,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.pool_strategy = pool_strategy
        self.outputs_name = output_feature
        self.inputs_name = None
        self.channel_axis = channel_axis
        self._default_channel_axis = -3

    def post_init(self):
        super().post_init()
        import paddlehub as hub
        module = hub.Module(name=self.model_name)
        inputs, outputs, self.model = module.context(trainable=False)
        self.get_inputs_and_outputs_name(inputs, outputs)
        self.exe = self.to_device()

    def close(self):
        self.exe.close()

    def get_inputs_and_outputs_name(self, input_dict, output_dict):
        raise NotImplementedError

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a `B x T x (Channel x Height x Width)` numpy ``ndarray``, `B` is the size of the batch, `T` is the
            number of frames
        :return: a `B x D` numpy ``ndarray``, `D` is the output dimension
        """
        if self.channel_axis != self._default_channel_axis:
            data = np.moveaxis(data, self.channel_axis, self._default_channel_axis)
        feature_map, *_ = self.exe.run(
            program=self.model,
            fetch_list=[self.outputs_name],
            feed={self.inputs_name: data.astype('float32')},
            return_numpy=True
        )
        if feature_map.ndim == 2 or self.pool_strategy is None:
            return feature_map
        return self.get_pooling(feature_map)

    def get_pooling(self, data: 'np.ndarray', axis=None) -> 'np.ndarray':
        _reduce_axis = tuple((i for i in range(len(data.shape)) if i > 1))
        return getattr(np, self.pool_strategy)(data, axis=_reduce_axis)
