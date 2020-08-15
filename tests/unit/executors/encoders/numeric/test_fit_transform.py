from jina.executors.encoders.numeric.fit_transform import RandomSparseEncoder, RandomGaussianEncoder, TSNEEncoder, \
    FeatureAgglomerationEncoder
from tests.unit.executors.encoders.numeric import NumericTestCase


class MyRandomGaussianEncoderTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = RandomGaussianEncoder(output_dim=self.target_output_dim)
        return encoder


class RandomSparseEncoderTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = RandomSparseEncoder(output_dim=self.target_output_dim)
        return encoder


class TSNEEncoderTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = TSNEEncoder(output_dim=self.target_output_dim)
        return encoder


class FeatureAgglomerationEncoderTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = FeatureAgglomerationEncoder(output_dim=self.target_output_dim)
        return encoder
