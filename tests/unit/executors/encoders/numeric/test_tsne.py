from jina.executors.encoders.numeric.tsne import TSNEEncoder
from tests.unit.executors.encoders.numeric import NumericTestCase


class TSNEEncoderTestCase(NumericTestCase):
    def _get_encoder(self):
        self.requires_train_after_load = False
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = TSNEEncoder(output_dim=self.target_output_dim)
        return encoder
