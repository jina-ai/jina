from jina.executors.encoders.numeric.random_sparse import RandomSparseEncoder
from tests.unit.executors.encoders.numeric import NumericTestCase


class RandomSparseEncoderTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = RandomSparseEncoder(output_dim=self.target_output_dim)
        return encoder
