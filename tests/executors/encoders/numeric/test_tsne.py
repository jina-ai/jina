import unittest

import numpy as np
from jina.executors.encoders.numeric.tsne import TSNEEncoder
from tests.executors.encoders.numeric import NumericTestCase


class MyTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        self.random_state = 2020 # Random State is necessary for reproducible results
        encoder = TSNEEncoder(output_dim=self.target_output_dim,random_state=self.random_state)
        return encoder


if __name__ == '__main__':
    unittest.main()
