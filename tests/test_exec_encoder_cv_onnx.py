import unittest

import os
import numpy as np

from jina.executors import BaseExecutor
from jina.executors.encoders.cv.onnx import OnnxImageEncoder
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    @unittest.skipIf(os.getenv('JINA_SKIP_TEST_PRETRAINED', True), 'skip the pretrained test if not set')
    def test_encoding_results(self):
        encoder = OnnxImageEncoder()
        test_data = np.random.rand(2, 3, 224, 224)
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape, (2, 1280))

    @unittest.skipIf(os.getenv('JINA_SKIP_TEST_PRETRAINED', True), 'skip the pretrained test if not set')
    def test_save_and_load(self):
        encoder = OnnxImageEncoder(model_fn='./onnx/mobilenetv2-1.0.raw')
        test_data = np.random.rand(2, 3, 224, 224)
        encoded_data_control = encoder.encode(test_data)
        encoder.touch()
        encoder.save()
        self.assertTrue(os.path.exists(encoder.save_abspath))
        encoder_loaded = BaseExecutor.load(encoder.save_abspath)
        encoded_data_test = encoder_loaded.encode(test_data)
        self.assertEqual(encoder_loaded.model_name, encoder.model_name)
        np.testing.assert_array_equal(encoded_data_control, encoded_data_test)
        self.add_tmpfile(
            encoder.config_abspath, encoder.save_abspath, encoder_loaded.config_abspath, encoder_loaded.save_abspath)

    @unittest.skipIf(os.getenv('JINA_SKIP_TEST_PRETRAINED', True), 'skip the pretrained test if not set')
    def test_save_and_load_config(self):
        encoder = OnnxImageEncoder(model_fn='./onnx/mobilenetv2-1.0.raw')
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))
        encoder_loaded = BaseExecutor.load_config(encoder.config_abspath)
        self.assertEqual(encoder_loaded.model_name, encoder.model_name)
        self.add_tmpfile(encoder_loaded.config_abspath, encoder_loaded.save_abspath, encoder.model_folder)


if __name__ == '__main__':
    unittest.main()


if __name__ == '__main__':
    unittest.main()
