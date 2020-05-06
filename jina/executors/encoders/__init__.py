__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Any

from .. import BaseExecutor, BasePaddleExecutor, BaseTorchExecutor
from ..compound import CompoundExecutor
from ..decorators import batching, as_ndarray

if False:
    # fix type-hint complain for sphinx and flake
    import numpy as np


class BaseEncoder(BaseExecutor):
    """``BaseEncoder`` encodes chunk into vector representation.

    The key function is :func:`encode`.

    .. seealso::
        :mod:`jina.drivers.handlers.encode`
    """

    def encode(self, data: Any, *args, **kwargs) -> Any:
        pass


class BaseNumericEncoder(BaseEncoder):
    """BaseNumericEncoder encodes data from a ndarray, potentially B x ([T] x D) into a ndarray of B x D"""

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """
        :param data: a `B x ([T] x D)` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``
        """
        pass


class BaseImageEncoder(BaseNumericEncoder):
    """BaseImageEncoder encodes data from a ndarray, potentially B x (Height x Width) into a ndarray of B x D"""
    pass


class BaseVideoEncoder(BaseNumericEncoder):
    """BaseVideoEncoder encodes data from a ndarray, potentially B x (Time x Height x Width) into a ndarray of B x D"""
    pass


class BaseAudioEncoder(BaseNumericEncoder):
    """BaseAudioEncoder encodes data from a ndarray, potentially B x (Time x D) into a ndarray of B x D"""
    pass


class BaseTextEncoder(BaseEncoder):
    """
    BaseTextEncoder encodes data from an array of string type (data.dtype.kind == 'U') of size B into a ndarray of B x D.

    """

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: an 1d array of string type (data.dtype.kind == 'U') in size B
        :return: an ndarray of `B x D`
        """
        pass


class PipelineEncoder(CompoundExecutor):
    def encode(self, data: Any, *args, **kwargs) -> Any:
        if not self.components:
            raise NotImplementedError
        for be in self.components:
            data = be.encode(data, *args, **kwargs)
        return data

    def train(self, data, *args, **kwargs):
        if not self.components:
            raise NotImplementedError
        for idx, be in enumerate(self.components):
            if not be.is_trained:
                be.train(data, *args, **kwargs)

            if idx + 1 < len(self.components):
                data = be.encode(data, *args, **kwargs)


class BaseCVPaddlehubEncoder(BasePaddleExecutor, BaseNumericEncoder):
    """
    :class:`BaseCVPaddlehubEncoder` implements the common parts for :class:`ImagePaddlehubEncoder` and
        :class:`VideoPaddlehubEncoder`.

    ..warning::
        :class:`BaseCVPaddlehubEncoder`  is not intented to be used to do the real encoding.
    """
    def __init__(self,
                 model_name: str,
                 output_feature: str,
                 pool_strategy: str = None,
                 channel_axis: int = -3,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.pool_strategy = pool_strategy
        self.outputs_name = output_feature
        self.inputs_name = None
        self.channel_axis = channel_axis
        self._default_channel_axis = -3

    def post_init(self):
        import paddlehub as hub
        module = hub.Module(name=self.model_name)
        inputs, outputs, self.model = module.context(trainable=False)
        self.get_inputs_and_outputs_name(inputs, outputs)

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


class BaseTorchEncoder(BaseTorchExecutor):
    """"
    :class:`BaseTorchEncoder` implements the common part for :class:`ImageTorchEncoder` and :class:`VideoTorchEncoder`.

    ..warning::
        :class:`BaseTorchEncoder`  is not intented to be used to do the real encoding.
    """
    def __init__(self,
                 model_name: str,
                 channel_axis: int = 1,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_name = model_name
        self.channel_axis = channel_axis
        self._default_channel_axis = 1

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        import numpy as np
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