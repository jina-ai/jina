import unittest

from tests import JinaTestCase
from jina.executors.encoders.clients import UnaryTFServingClientEncoder


class MyTestCase(JinaTestCase):
    @unittest.skip('add grpc mocking for this test')
    def test_mnist_predict(self):
        class MnistTFServingClientEncoder(UnaryTFServingClientEncoder):
            def __init__(self, *args, **kwargs):
                super().__init__(input_name='images', output_name='scores', model_name='mnist', *args, **kwargs)
                self.host = '0.0.0.0'
                self.port = '8500'
                self.method_name = 'Predict'
                self.signature_name = 'predict_images'
        import numpy as np
        encoder = MnistTFServingClientEncoder()
        data = np.random.rand(1, 784)
        result = encoder.encode(data)
        self.assertEqual(result.shape, (10, ))


if __name__ == '__main__':
    unittest.main()
