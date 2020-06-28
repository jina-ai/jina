import unittest

import numpy as np
from jina.executors.encoders.numeric.featureagglomerate import FeatureAgglomerationEncoder
from tests.executors.encoders.numeric import NumericTestCase


class MyTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = FeatureAgglomerationEncoder(output_dim=self.target_output_dim)
        return encoder


if __name__ == '__main__':
    unittest.main()
