import os
import unittest

import numpy as np
from jina.executors import BaseExecutor
from tests.unit.executors import ExecutorTestCase


class ImageTestCase(ExecutorTestCase):
    @property
    def workspace(self):
        return os.path.join(os.environ['TEST_WORKDIR'], 'test_tmp')

    @property
    def target_output_dim(self):
        return self._target_output_dim

    @target_output_dim.setter
    def target_output_dim(self, output_dim):
        self._target_output_dim = output_dim

    @property
    def input_dim(self):
        return self._input_dim

    @input_dim.setter
    def input_dim(self, input_dim):
        self._input_dim = input_dim

    def get_encoder(self):
        encoder = self._get_encoder(self.metas)
        if encoder is not None:
            encoder.workspace = self.workspace
            self.add_tmpfile(encoder.workspace)
        return encoder

    def _get_encoder(self, metas):
        return None

    @unittest.skipUnless('JINA_TEST_PRETRAINED' in os.environ, 'skip the pretrained test if not set')
    def test_encoding_results(self):
        encoder = self.get_encoder()
        if encoder is None:
            return
        test_data = np.random.rand(2, 3, self.input_dim, self.input_dim)
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape, (2, self.target_output_dim))

    @unittest.skipUnless('JINA_TEST_PRETRAINED' in os.environ, 'skip the pretrained test if not set')
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

    @unittest.skipUnless('JINA_TEST_PRETRAINED' in os.environ, 'skip the pretrained test if not set')
    def test_save_and_load_config(self):
        encoder = self.get_encoder()
        if encoder is None:
            return
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))
        encoder_loaded = BaseExecutor.load_config(encoder.config_abspath)
        self.assertEqual(encoder_loaded.channel_axis, encoder.channel_axis)
