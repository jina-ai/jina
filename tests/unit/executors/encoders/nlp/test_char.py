import os
import unittest

import numpy as np
from jina.executors import BaseExecutor
from jina.executors.encoders.nlp.char import OneHotTextEncoder
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    def test_encoding_results(self):
        encoder = OneHotTextEncoder(workspace=os.environ['TEST_WORKDIR'])
        test_data = np.array(['a', 'b', 'c', 'x', '!'])
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape, (5, 97))
        self.assertIs(type(encoded_data), np.ndarray)

    def test_save_and_load(self):
        encoder = OneHotTextEncoder(workspace=os.environ['TEST_WORKDIR'])
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))
        test_data = np.array(['a', 'b', 'c', 'x', '!'])
        encoded_data_control = encoder.encode(test_data)

        encoder.touch()
        encoder.save()
        self.assertTrue(os.path.exists(encoder.save_abspath))
        encoder_loaded = BaseExecutor.load(encoder.save_abspath)
        encoded_data_test = encoder_loaded.encode(test_data)

        np.testing.assert_array_equal(encoded_data_control, encoded_data_test)
        self.assertEqual(encoder_loaded.dim, encoder.dim)

        self.add_tmpfile(
            encoder.config_abspath, encoder.save_abspath, encoder_loaded.config_abspath, encoder_loaded.save_abspath)

    def test_save_and_load_config(self):
        encoder = OneHotTextEncoder(workspace=os.environ['TEST_WORKDIR'])
        encoder.save_config()
        self.assertTrue(os.path.exists(encoder.config_abspath))

        encoder_loaded = BaseExecutor.load_config(encoder.config_abspath)
        self.assertEqual(encoder_loaded.dim, encoder.dim)

        self.add_tmpfile(encoder_loaded.config_abspath, encoder_loaded.save_abspath)


if __name__ == '__main__':
    unittest.main()
