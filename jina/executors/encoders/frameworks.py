__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os

from . import BaseEncoder
from ..devices import OnnxDevice, PaddleDevice, TorchDevice, TFDevice, MindsporeDevice
from ...excepts import ModelCheckpointNotExist
from ...helper import is_url, cached_property


# mixin classes go first, base classes are read from right to left.
class BaseOnnxEncoder(OnnxDevice, BaseEncoder):
    def __init__(self, output_feature: str = None, model_path: str = None, *args, **kwargs):
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
        super().post_init()
        model_name = self.raw_model_path.split('/')[-1] if self.raw_model_path else None
        tmp_model_path = self.get_file_from_workspace(f'{model_name}.tmp') if model_name else None
        raw_model_path = self.raw_model_path
        if self.raw_model_path and is_url(self.raw_model_path):
            import urllib.request
            download_path, *_ = urllib.request.urlretrieve(self.raw_model_path)
            raw_model_path = download_path
            self.logger.info(f'download the model at {self.raw_model_path}')
        if tmp_model_path and not os.path.exists(tmp_model_path) and self.outputs_name:
            self._append_outputs(raw_model_path, self.outputs_name, tmp_model_path)
            self.logger.info(f'save the model with outputs [{self.outputs_name}] at {tmp_model_path}')

        if tmp_model_path and os.path.exists(tmp_model_path):
            import onnxruntime
            self.model = onnxruntime.InferenceSession(tmp_model_path, None)
            self.inputs_name = self.model.get_inputs()[0].name
            self._device = None
            self.to_device(self.model)
        else:
            raise ModelCheckpointNotExist(f'model at {tmp_model_path} does not exist')

    @staticmethod
    def _append_outputs(input_fn, outputs_name_to_append, output_fn):
        import onnx
        model = onnx.load(input_fn)
        feature_map = onnx.helper.ValueInfoProto()
        feature_map.name = outputs_name_to_append
        model.graph.output.append(feature_map)
        onnx.save(model, output_fn)


class BaseTFEncoder(TFDevice, BaseEncoder):
    pass


class BaseTorchEncoder(TorchDevice, BaseEncoder):
    pass


class BasePaddleEncoder(PaddleDevice, BaseEncoder):
    pass


class BaseMindsporeEncoder(MindsporeDevice, BaseEncoder):
    """
    :class:`BaseMindsporeEncoder` is the base class for implementing Encoders with models from `mindspore`.

    To implement your own executor with the :mod:`mindspore` lilbrary,

    .. highlight:: python
    .. code-block:: python
        import mindspore.nn as nn

        class YourAwesomeModel(nn.Cell):
            def __init__(self):
                ...

            def construct(self, x):
                ...

        class YourAwesomeEncoder(BaseMindsporeEncoder):
            def encode(self, data, *args, **kwargs):
                from mindspore import Tensor
                return self.model(Tensor(data)).asnumpy()

            def get_cell(self):
                return YourAwesomeModel()

    """

    def __init__(self, model_path: str = None, *args, **kwargs):
        """

        :param model_path: the path of the model's checkpoint.
        """
        super().__init__(*args, **kwargs)
        self.model_path = model_path

    def post_init(self):
        """
        Load the model from the `.ckpt` checkpoint.
        """
        super().post_init()
        if self.model_path and os.path.exists(self.model_path):
            self.to_device()
            from mindspore.train.serialization import load_checkpoint, load_param_into_net
            _param_dict = load_checkpoint(ckpt_file_name=self.model_path)
            load_param_into_net(self.model, _param_dict)
        else:
            raise ModelCheckpointNotExist(f'model {self.model_path} does not exist')

    @cached_property
    def model(self):
        return self.get_cell()

    def get_cell(self):
        """
        Return Mindspore Neural Networks Cells.

        Pre-defined building blocks or computing units to construct Neural Networks.
        A ``Cell`` could be a single neural network cell, such as conv2d, relu, batch_norm, etc.
        or a composition of cells to constructing a network.

        :return: :class:`mindspore.nn.Cell`
        """
        raise NotImplementedError
