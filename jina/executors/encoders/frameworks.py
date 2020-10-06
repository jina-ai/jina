__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os

from . import BaseEncoder
from ..devices import OnnxDevice, PaddleDevice, TorchDevice, TFDevice, MindsporeDevice
from ...helper import is_url
from ...helper import cached_property


# mixin classes go first, base classes are read from right to left.
class BaseOnnxEncoder(OnnxDevice, BaseEncoder):
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
        super().post_init()
        self.model_name = self.raw_model_path.split('/')[-1]
        self.tmp_model_path = self.get_file_from_workspace(f'{self.model_name}.tmp')
        if is_url(self.raw_model_path):
            import urllib.request
            download_path, *_ = urllib.request.urlretrieve(self.raw_model_path)
            self.raw_model_path = download_path
            self.logger.info(f'download the model at {self.raw_model_path}')
        if not os.path.exists(self.tmp_model_path):
            self._append_outputs(self.raw_model_path, self.outputs_name, self.tmp_model_path)
            self.logger.info(f'save the model with outputs [{self.outputs_name}] at {self.tmp_model_path}')
        self.model = onnxruntime.InferenceSession(self.tmp_model_path, None)
        self.inputs_name = self.model.get_inputs()[0].name
        self._device = None
        self.to_device(self.model)

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

            def get_model(self):
                return YourAwesomeModel()

    """
    def __init__(self, model_path: str, *args, **kwargs):
        """

        :param model_path: the path of the model's checkpoint.
        """
        super().__init__(*args, **kwargs)
        self.model_path = model_path

    def post_init(self):
        """
        Load the model from the `.ckpt` checkpoint.
        """
        from mindspore.train.serialization import load_checkpoint, load_param_into_net
        super().post_init()
        self.to_device()
        _param_dict = load_checkpoint(ckpt_file_name=self.model_path)
        load_param_into_net(self.model, _param_dict)

    @cached_property
    def model(self):
        return self.get_model()

    def get_model(self):
        raise NotImplemented('the model is not implemented')
