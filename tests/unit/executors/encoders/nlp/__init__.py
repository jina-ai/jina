import os
import unittest

import numpy as np
from jina.executors import BaseExecutor
from tests.unit.executors import ExecutorTestCase


class NlpTestCase(ExecutorTestCase):
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
        test_data = np.array(['it is a good day!', 'the dog sits on the floor.'])
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape[0], 2)

    @unittest.skipUnless('JINA_TEST_PRETRAINED' in os.environ, 'skip the pretrained test if not set')
    def test_save_and_load(self):
        encoder = self.get_encoder()
        if encoder is None:
            return
        test_data = np.array(['it is a good day!', 'the dog sits on the floor.'])
        encoded_data_control = encoder.encode(test_data)
        encoder.touch()
        encoder.save()
        self.assertTrue(os.path.exists(encoder.save_abspath))
        encoder_loaded = BaseExecutor.load(encoder.save_abspath)
        encoded_data_test = encoder_loaded.encode(test_data)
        self.assertEqual(encoder_loaded.max_length, encoder.max_length)
        np.testing.assert_array_equal(encoded_data_control, encoded_data_test)

    @unittest.skipUnless('JINA_TEST_PRETRAINED' in os.environ, 'skip the pretrained test if not set')
    def test_save_and_load_config(self):
        encoder = self.get_encoder()
        if encoder is None:
            return
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))
        encoder_loaded = BaseExecutor.load_config(encoder.config_abspath)
        self.assertEqual(encoder_loaded.max_length, encoder.max_length)
