import unittest
import numpy as np
import os
import sys

from tests import JinaTestCase
from jina.executors.encoders.ernie import ErnieTextEncoder
from jina.executors import BaseExecutor


class MyTestCase(JinaTestCase):
    @unittest.skip("skip tests depending on pretraining models")
    def test_encoding_results(self):
        encoder = ErnieTextEncoder(max_length=10, workspace=os.environ['TEST_WORKDIR'])
        test_data = np.array(['it is a good day!', 'the dog sits on the floor.'])
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape[0], 2)
        self.assertIs(type(encoded_data), np.ndarray)
        self.add_tmpfile(encoder.vocab_filename)

    @unittest.skipIf(sys.version_info >= (3, 8, 0), "paddlepaddle doesn't support python >= 3.8.0")
    def test_save_and_load(self):
        encoder = ErnieTextEncoder(
            max_length=10, workspace=os.environ['TEST_WORKDIR'])
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))
        test_data = np.array(['it is a good day!', 'the dog sits on the floor.'])
        encoded_data_control = encoder.encode(test_data)

        encoder.touch()
        encoder.save()
        self.assertTrue(os.path.exists(encoder.save_abspath))
        encoder_loaded = BaseExecutor.load(encoder.save_abspath)
        encoded_data_test = encoder_loaded.encode(test_data)

        self.assertEqual(encoder_loaded.vocab_filename, encoder.vocab_filename)

        self.add_tmpfile(
            encoder.config_abspath, encoder.save_abspath, encoder_loaded.config_abspath, encoder_loaded.save_abspath, encoder.vocab_filename)

    @unittest.skipIf(sys.version_info >= (3, 8, 0), "paddlepaddle doesn't support python >= 3.8.0")
    def test_save_and_load_config(self):
        encoder = ErnieTextEncoder(
            max_length=10, workspace=os.environ['TEST_WORKDIR'])
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))

        encoder_loaded = BaseExecutor.load_config(encoder.config_abspath)
        self.assertEqual(encoder_loaded.vocab_filename, encoder.vocab_filename)

        self.add_tmpfile(encoder_loaded.config_abspath, encoder_loaded.save_abspath, encoder.vocab_filename)


if __name__ == '__main__':
    unittest.main()
