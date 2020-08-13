import unittest

import numpy as np
from jina.executors.encoders.numeric.fit_transform import RandomSparseEncoder, RandomGaussianEncoder, TSNEEncoder, FeatureAgglomerationEncoder
from tests.executors.encoders.numeric import NumericTestCase


class MyTestCaseRandomGaussianEncoder(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = RandomGaussianEncoder(output_dim=self.target_output_dim)
        return encoder

class MyTestCaseRandomSparseEncoder(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = RandomSparseEncoder(output_dim=self.target_output_dim)
        return encoder

class MyTestCaseTSNEEncoder(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = TSNEEncoder(output_dim=self.target_output_dim)
        return encoder

class MyTestCaseFeatureAgglomerationEncoder(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = FeatureAgglomerationEncoder(output_dim=self.target_output_dim)
        return encoder

if __name__ == '__main__':
    unittest.main()
