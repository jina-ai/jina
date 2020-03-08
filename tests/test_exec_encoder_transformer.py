import unittest
import numpy as np
from tests import JinaTestCase
from jina.executors.encoders.transformer import PyTorchTransformers


class MyTestCase(JinaTestCase):
    def test_encoding_results(self):
        encoder = PyTorchTransformers()
        test_data = np.array(['a', 'b', 'xy'])
        encoded_data = encoder.encode(test_data)
        self.assertEqual(encoded_data.shape[0], 3)
        self.assertIs(type(encoded_data), np.ndarray)

    def test_all_encoders(self):
        from jina.executors.encoders.transformer import MODELS
        for model_name in MODELS:
            print("{}".format(model_name))
            encoder = PyTorchTransformers(model_name)
            test_data = np.array(['a', 'b', 'xy'])
            encoded_data = encoder.encode(test_data)
            self.assertEqual(encoded_data.shape[0], 3, '{} failed'.format(model_name))


if __name__ == '__main__':
    unittest.main()
