import os
import unittest

import numpy as np

from jina.executors import BaseExecutor
from tests import JinaTestCase


class ImageTestCase(JinaTestCase):
    @property
    def target_output_dim(self):
        return self._target_output_dim

    @target_output_dim.setter
    def target_output_dim(self, output_dim):
        self._target_output_dim = output_dim

    @unittest.skipUnless('JINA_TEST_PRETRAINED' in os.environ, 'skip the pretrained test if not set')
    def test_encoding_results(self):
        encoder = self.get_encoder()
        test_data = np.random.rand(2, 3, 224, 224)
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape, (2, self._target_output_dim))

    @unittest.skipUnless('JINA_TEST_PRETRAINED' in os.environ, 'skip the pretrained test if not set')
    def test_save_and_load(self):
        encoder = self.get_encoder()
        test_data = np.random.rand(2, 3, 224, 224)
        encoded_data_control = encoder.encode(test_data)
        encoder.touch()
        encoder.save()
        self.assertTrue(os.path.exists(encoder.save_abspath))
        encoder_loaded = BaseExecutor.load(encoder.save_abspath)
        encoded_data_test = encoder_loaded.encode(test_data)
        self.assertEqual(encoder_loaded.pool_strategy, encoder.pool_strategy)
        np.testing.assert_array_equal(encoded_data_control, encoded_data_test)
        self.add_tmpfile(
            encoder.config_abspath, encoder.save_abspath, encoder_loaded.config_abspath, encoder_loaded.save_abspath)

    @unittest.skipUnless('JINA_TEST_PRETRAINED' in os.environ, 'skip the pretrained test if not set')
    def test_save_and_load_config(self):
        encoder = self.get_encoder()
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))
        encoder_loaded = BaseExecutor.load_config(encoder.config_abspath)
        self.assertEqual(encoder_loaded.pool_strategy, encoder.pool_strategy)
        self.add_tmpfile(encoder_loaded.config_abspath, encoder_loaded.save_abspath)

    def get_encoder(self, model_path=None):
        raise NotImplementedError
