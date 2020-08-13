import tempfile
import os

import numpy as np

from jina.executors.encoders.image.mindspore import CustomMindsporeImageEncoder
from tests.unit.executors.encoders.image import ImageTestCase
from jina.executors import BaseExecutor


class CustomMindsporeTestCase(ImageTestCase):
    def _get_encoder(self, metas):
        import mindspore.nn as nn
        from mindspore import Tensor, Parameter
        from mindspore.ops import operations as P
        from mindspore.train.serialization import save_checkpoint
        import mindspore

        self.target_output_dim = 5
        self.input_dim = 16
        kernel_size = 4
        conv_output_channel = 8

        class TestNet(nn.Cell):
            def __init__(self):
                super(TestNet, self).__init__()
                self.conv_weight = Parameter(Tensor(
                    np.ones([conv_output_channel, 3, kernel_size, kernel_size]), mindspore.float32), "conv_weight")
                self.conv2d = P.Conv2D(out_channel=conv_output_channel, kernel_size=kernel_size)
                self.flatten = P.Flatten()
                self.fc_weight = Parameter(Tensor(
                    np.ones([1352, self.target_output_dim]), mindspore.float32), "fc_weight")
                self.fc = P.MatMul()

            def construct(self, x):
                x = self.conv2d(x, self.conv_weight)
                x = self.flatten(x)
                x = self.fc(x, self.fc_weight)
                return x

        net = TestNet()
        param_dict = {}
        for _, param in net.parameters_and_names():
            param_dict[param.name] = param
        param_list = []
        for (key, value) in param_dict.items():
            each_param = {}
            each_param["name"] = key
            if isinstance(value.data, Tensor):
                param_data = value.data
            else:
                param_data = Tensor(value.data)
            each_param["data"] = param_data
            param_list.append(each_param)

        path = tempfile.NamedTemporaryFile().name
        self.add_tmpfile(path)
        save_checkpoint(param_list, path)

        return CustomMindsporeImageEncoder(model_name='TestNet', model_path=path)

    def test_encoding_results(self):
        encoder = self.get_encoder()
        if encoder is None:
            return
        test_data = np.random.rand(2, 3, self.input_dim, self.input_dim)
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape, (2, self.target_output_dim))

    def test_save_and_load(self):
        encoder = self.get_encoder()
        if encoder is None:
            return
        test_data = np.random.rand(2, 3, self.input_dim, self.input_dim)
        encoded_data_control = encoder.encode(test_data)
        encoder.touch()
        encoder.save()
        self.assertTrue(os.path.exists(encoder.save_abspath))
        encoder_loaded = BaseExecutor.load(encoder.save_abspath)
        encoded_data_test = encoder_loaded.encode(test_data)
        self.assertEqual(encoder_loaded.channel_axis, encoder.channel_axis)
        np.testing.assert_array_equal(encoded_data_control, encoded_data_test)

    def test_save_and_load_config(self):
        encoder = self.get_encoder()
        if encoder is None:
            return
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))
        encoder_loaded = BaseExecutor.load_config(encoder.config_abspath)
        self.assertEqual(encoder_loaded.channel_axis, encoder.channel_axis)
