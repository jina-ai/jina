import unittest

from tests import JinaTestCase
from jina.executors.encoders.clients import UnaryTFServingEncoder


class MyTestCase(JinaTestCase):
    @unittest.skip('add grpc mocking for this test')
    def test_something(self):
        encoder = UnaryTFServingEncoder(
            host='0.0.0.0', port='8500', service_name='mnist',
            input_name='images', output_name='scores',
            signature_name='predict_images')
        import numpy as np
        data = np.random.rand(1, 784)
        result = encoder.encode(data)
        self.assertEqual(result.shape, (10, ))


if __name__ == '__main__':
    unittest.main()
