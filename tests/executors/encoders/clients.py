import unittest

from tests import JinaTestCase
from jina.executors.encoders.clients import TFServingEncoder


class MyTestCase(JinaTestCase):
    @unittest.skip('add grpc mocking for this test')
    def test_something(self):
        encoder = TFServingEncoder(
            host='0.0.0.0', port='8500', input_name='images', output_name='scores', signature_name='predict_images', name='mnist')
        import numpy as np
        data = np.random.rand(1, 784).astype(np.float32)
        result = encoder.encode(data)
        self.assertEqual(result.shape, (10, ))


if __name__ == '__main__':
    unittest.main()
