import unittest

import numpy as np
import os

from . import JinaTestCase
from jina.executors.encoders.numeric.pca import IncrementalPCAEncoder
from jina.executors import BaseExecutor


class MyTestCase(JinaTestCase):
    num_features = 28
    output_dim = 2

    def test_encoding_results(self):
        encoder = IncrementalPCAEncoder(
            output_dim=self.output_dim, whiten=True, num_features=self.num_features)
        train_data = np.random.rand(1000, self.num_features)
        encoder.train(train_data)
        self.assertTrue(encoder.is_trained)

        test_data = np.random.rand(10, self.num_features)
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape, (test_data.shape[0], self.output_dim))
        self.assertIs(type(encoded_data), np.ndarray)

    def test_save_and_load(self):
        encoder = IncrementalPCAEncoder(
            output_dim=self.output_dim, whiten=True, num_features=self.num_features)
        train_data = np.random.rand(1000, self.num_features)
        encoder.train(train_data)
        test_data = np.random.rand(10, self.num_features)
        encoded_data_control = encoder.encode(test_data)

        encoder.touch()
        encoder.save()
        self.assertTrue(os.path.exists(encoder.save_abspath))
        encoder_loaded = BaseExecutor.load(encoder.save_abspath)
        encoded_data_test = encoder_loaded.encode(test_data)

        self.assertEqual(
            encoder_loaded.model.n_samples_seen_,
            encoder.model.n_samples_seen_)
        np.testing.assert_array_equal(
            encoded_data_test, encoded_data_control)
        self.add_tmpfile(
            encoder.config_abspath, encoder.save_abspath, encoder_loaded.config_abspath, encoder_loaded.save_abspath,
            encoder.encoder_abspath)

    def test_save_and_load_config(self):
        encoder = IncrementalPCAEncoder(
            output_dim=self.output_dim, whiten=True, num_features=self.num_features)
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))

        encoder_loaded = BaseExecutor.load_config(encoder.config_abspath)

        self.assertEqual(
            encoder_loaded.output_dim,
            encoder.output_dim)

        self.add_tmpfile(encoder_loaded.config_abspath, encoder_loaded.save_abspath)


if __name__ == '__main__':
    unittest.main()
