import os
import unittest

import numpy as np

from jina.executors import BaseExecutor
from jina.executors.encoders.nlp.ernie import ErnieTextEncoder
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    @unittest.skipUnless('JINA_TEST_PRETRAINED' in os.environ, 'skip the pretrained test if not set')
    def test_encoding_results(self):
        encoder = ErnieTextEncoder(max_length=10, workspace=os.environ['TEST_WORKDIR'])
        test_data = np.array(['it is a good day!', 'the dog sits on the floor.'])
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape[0], 2)
        self.assertIs(type(encoded_data), np.ndarray)
        self.add_tmpfile(encoder.vocab_abspath)

    @unittest.skipUnless('JINA_TEST_PRETRAINED' in os.environ, 'skip the pretrained test if not set')
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

        self.assertEqual(encoder_loaded.vocab_abspath, encoder.vocab_abspath)

        self.add_tmpfile(
            encoder.config_abspath, encoder.save_abspath, encoder_loaded.config_abspath, encoder_loaded.save_abspath, encoder.vocab_abspath)

    @unittest.skipUnless('JINA_TEST_PRETRAINED' in os.environ, 'skip the pretrained test if not set')
    def test_save_and_load_config(self):
        encoder = ErnieTextEncoder(
            max_length=10, workspace=os.environ['TEST_WORKDIR'])
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))

        encoder_loaded = BaseExecutor.load_config(encoder.config_abspath)
        self.assertEqual(encoder_loaded.vocab_abspath, encoder.vocab_abspath)

        self.add_tmpfile(encoder_loaded.config_abspath, encoder_loaded.save_abspath, encoder.vocab_abspath)


if __name__ == '__main__':
    unittest.main()
