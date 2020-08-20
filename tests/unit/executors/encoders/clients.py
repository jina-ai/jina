import os
import pytest

import numpy as np
from jina.executors import BaseExecutor
from jina.executors.encoders.tfserving import UnaryTFServingClientEncoder
from tests import JinaTestCase


class MnistTFServingClientEncoder(UnaryTFServingClientEncoder):
    def __init__(self, *args, **kwargs):
        default_kwargs = dict(
            host='0.0.0.0', port='8500', method_name='Predict', signature_name='predict_images',
            input_name='images', output_name='scores', model_name='mnist')
        kwargs.update(default_kwargs)
        super().__init__(*args, **kwargs)


@pytest.mark.skip('add grpc mocking for this test')
class MyTestCase(JinaTestCase):
    @property
    def workspace(self):
        return os.path.join(os.environ['TEST_WORKDIR'], 'test_tmp')

    def get_encoder(self):
        encoder = MnistTFServingClientEncoder()
        encoder.workspace = self.workspace
        self.add_tmpfile(encoder.workspace)
        return encoder

    def test_mnist_encoding(self):
        encoder = self.get_encoder()
        data = np.random.rand(1, 784)
        result = encoder.encode(data)
        assert result.shape == (10, )

    def test_save_and_load(self):
        encoder = self.get_encoder()
        data = np.random.rand(1, 784)
        encoded_data_control = encoder.encode(data)
        encoder.touch()
        encoder.save()
        self.assertTrue(os.path.exists(encoder.save_abspath))
        encoder_loaded = BaseExecutor.load(encoder.save_abspath)
        encoded_data_test = encoder_loaded.encode(data)
        np.testing.assert_array_equal(encoded_data_control, encoded_data_test)

    def test_save_and_load_config(self):
        encoder = self.get_encoder()
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))
        encoder_loaded = BaseExecutor.load_config(encoder.config_abspath)
        assert encoder_loaded.model_name == encoder.model_name
