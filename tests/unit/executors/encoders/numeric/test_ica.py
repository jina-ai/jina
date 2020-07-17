import unittest

import numpy as np
from jina.executors.encoders.numeric.ica import FastICAEncoder
from tests.unit.executors.encoders.numeric import NumericTestCase


class MyTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 200
        self.target_output_dim = 7
        encoder = FastICAEncoder(
            output_dim=self.target_output_dim, whiten=True, num_features=self.input_dim)
        train_data = np.random.rand(2000, self.input_dim)
        encoder.train(train_data)
        return encoder


if __name__ == '__main__':
    unittest.main()