from jina.executors.encoders.numeric.random_gaussian import RandomGaussianEncoder
from tests.unit.executors.encoders.numeric import NumericTestCase


class RandomGaussianEncoderTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = RandomGaussianEncoder(output_dim=self.target_output_dim)
        return encoder
