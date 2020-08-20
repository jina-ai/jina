import os

import numpy as np
from jina.executors import BaseExecutor
from tests import JinaTestCase


class NumericTestCase(JinaTestCase):
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
    def requires_train_after_load(self):
        return self._requires_train_after_load

    @requires_train_after_load.setter
    def requires_train_after_load(self, train_after_load):
        self._requires_train_after_load = train_after_load

    @property
    def input_dim(self):
        return self._input_dim

    @input_dim.setter
    def input_dim(self, input_dim):
        self._input_dim = input_dim

    @property
    def train_data(self):
        return self._train_data

    @train_data.setter
    def train_data(self, train_data):
        self._train_data = train_data

    def get_encoder(self):
        encoder = self._get_encoder()
        if encoder is not None:
            encoder.workspace = self.workspace
            self.add_tmpfile(encoder.workspace)
        return encoder

    def _get_encoder(self):
        return None

    def test_encoding_results(self):
        encoder = self.get_encoder()
        if encoder is None:
            return
        test_data = np.random.rand(10, self.input_dim)
        encoded_data = encoder.encode(test_data)
        assert encoded_data.shape == (test_data.shape[0], self.target_output_dim)
        self.assertIs(type(encoded_data), np.ndarray)

    def test_save_and_load(self):
        encoder = self.get_encoder()
        if encoder is None:
            return
        test_data = np.random.rand(10, self.input_dim)
        encoded_data_control = encoder.encode(test_data)
        encoder.touch()
        encoder.save()
        self.assertTrue(os.path.exists(encoder.save_abspath))
        encoder_loaded = BaseExecutor.load(encoder.save_abspath)

        if not self.requires_train_after_load:
            # some models are not deterministic when training, so even with same training data, we cannot ensure
            # same encoding results
            encoded_data_test = encoder_loaded.encode(test_data)
            np.testing.assert_array_equal(
                encoded_data_test, encoded_data_control)

    def test_save_and_load_config(self):
        encoder = self.get_encoder()
        if encoder is None:
            return
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))
        encoder_loaded = BaseExecutor.load_config(encoder.config_abspath)

        if self.requires_train_after_load:
            encoder_loaded.train(self.train_data)

        test_data = np.random.rand(10, self.input_dim)
        encoded_data_test = encoder_loaded.encode(test_data)
        assert encoded_data_test.shape == (10, self.target_output_dim)
