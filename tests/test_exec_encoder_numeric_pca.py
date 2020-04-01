import unittest

import numpy as np
import os

from tests import JinaTestCase
import jina.executors.encoders.numeric.pca as pca
from jina.executors import BaseExecutor


class MyTestCase(JinaTestCase):
    num_features = 28
    output_dim = 2
    model_list = ('IncrementalPCAEncoder', 'PCAEncoder')

    def _test_encoding_results(self, encoder):
        train_data = np.random.rand(1000, self.num_features)
        encoder.train(train_data)
        self.assertTrue(encoder.is_trained)
        test_data = np.random.rand(10, self.num_features)
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape, (test_data.shape[0], self.output_dim))
        self.assertIs(type(encoded_data), np.ndarray)
        self.add_tmpfile(encoder.config_abspath, encoder.save_abspath)
        if hasattr(encoder, 'model_abspath'):
            self.add_tmpfile(encoder.model_abspath)

    def test_encoding_results(self):
        for m in self.model_list:
            encoder = getattr(pca, m)(
                output_dim=self.output_dim, whiten=True, num_features=self.num_features)
            self._test_encoding_results(encoder)

    def _test_save_and_load(self, encoder):
        train_data = np.random.rand(1000, self.num_features)
        encoder.train(train_data)
        test_data = np.random.rand(10, self.num_features)
        encoded_data_control = encoder.encode(test_data)
        encoder.touch()
        encoder.save()
        self.assertTrue(os.path.exists(encoder.save_abspath))
        encoder_loaded = BaseExecutor.load(encoder.save_abspath)
        encoded_data_test = encoder_loaded.encode(test_data)
        np.testing.assert_array_equal(
            encoded_data_test, encoded_data_control)
        self.add_tmpfile(encoder.config_abspath, encoder.save_abspath)
        if hasattr(encoder, 'model_abspath'):
            self.add_tmpfile(encoder.model_abspath)

    def test_save_and_load(self):
        for m in self.model_list:
            encoder = getattr(pca, m)(
                output_dim=self.output_dim, whiten=True, num_features=self.num_features)
            self._test_save_and_load(encoder)

    def _test_save_and_load_config(self, encoder):
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))
        encoder_loaded = BaseExecutor.load_config(encoder.config_abspath)
        self.assertEqual(
            encoder_loaded.output_dim,
            encoder.output_dim)
        self.add_tmpfile(encoder.config_abspath, encoder.save_abspath)
        if hasattr(encoder, 'model_abspath'):
            self.add_tmpfile(encoder.model_abspath)

    def test_save_and_load_config(self):
        for m in self.model_list:
            encoder = getattr(pca, m)(
                output_dim=self.output_dim, whiten=True, num_features=self.num_features)
            self._test_save_and_load_config(encoder)


if __name__ == '__main__':
    unittest.main()
