__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os

import numpy as np

from . import BaseEncoder
from ..decorators import batching, as_ndarray
from ..frameworks import BaseOnnxExecutor, BasePaddleExecutor, BaseTorchExecutor, BaseTFExecutor
from ...helper import is_url


class BaseOnnxEncoder(BaseOnnxExecutor, BaseEncoder):
    def __init__(self, output_feature: str, model_path: str = None, *args, **kwargs):
        """

        :param output_feature: the name of the layer for feature extraction.
        :param model_path: the path of the model in the format of `.onnx`. Check a list of available pretrained
            models at https://github.com/onnx/models#image_classification and download the git LFS to your local path.
            The ``model_path`` is the local path of the ``.onnx`` file, e.g. ``/tmp/onnx/mobilenetv2-1.0.onnx``.
        """
        super().__init__(*args, **kwargs)
        self.outputs_name = output_feature
        self.raw_model_path = model_path

    def post_init(self):
        """
        Load the model from the `.onnx` file and add outputs for the selected layer, i.e. ``outputs_name``. The modified
             models is saved at `tmp_model_path`.
        """
        import onnxruntime
        self.model_name = self.raw_model_path.split('/')[-1]
        self.tmp_model_path = self.get_file_from_workspace(f'{self.model_name}.tmp')
        if is_url(self.raw_model_path):
            import urllib.request
            download_path, *_ = urllib.request.urlretrieve(self.raw_model_path)
            self.raw_model_path = download_path
            self.logger.info('download the model at {}'.format(self.raw_model_path))
        if not os.path.exists(self.tmp_model_path):
            self._append_outputs(self.raw_model_path, self.outputs_name, self.tmp_model_path)
            self.logger.info('save the model with outputs [{}] at {}'.format(self.outputs_name, self.tmp_model_path))
        self.model = onnxruntime.InferenceSession(self.tmp_model_path, None)
        self.inputs_name = self.model.get_inputs()[0].name
        self.to_device(self.model)

    @staticmethod
    def _append_outputs(input_fn, outputs_name_to_append, output_fn):
        import onnx
        model = onnx.load(input_fn)
        feature_map = onnx.helper.ValueInfoProto()
        feature_map.name = outputs_name_to_append
        model.graph.output.append(feature_map)
        onnx.save(model, output_fn)


class BaseTFEncoder(BaseTFExecutor, BaseEncoder):
    pass


class BaseTorchEncoder(BaseTorchExecutor, BaseEncoder):
    pass


class BasePaddlehubEncoder(BasePaddleExecutor, BaseEncoder):
    pass


class BaseTextTFEncoder(BaseTFEncoder):
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: an 1d array of string type (data.dtype.kind == 'U') in size B
        :return: an ndarray of `B x D`
        """
        pass


class BaseTextTorchEncoder(BaseTorchEncoder):
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: an 1d array of string type (data.dtype.kind == 'U') in size B
        :return: an ndarray of `B x D`
        """
        pass


class BaseTextPaddlehubEncoder(BasePaddlehubEncoder):
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: an 1d array of string type (data.dtype.kind == 'U') in size B
        :return: an ndarray of `B x D`
        """
        pass


class BaseCVTFEncoder(BaseTFEncoder):
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """
        :param data: a `B x ([T] x D)` numpy ``ndarray``, `B` is the size of the batch
        :return: a `B x D` numpy ``ndarray``
        """
        pass


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


class BaseCVPaddlehubEncoder(BasePaddlehubEncoder):
    """
    :class:`BaseCVPaddlehubEncoder` implements the common parts for :class:`ImagePaddlehubEncoder` and
        :class:`VideoPaddlehubEncoder`.

    ..warning::
        :class:`BaseCVPaddlehubEncoder`  is not intented to be used to do the real encoding.
    """

    def __init__(self,
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
