from jina.executors.encoders.numeric.feature_agglomeration import FeatureAgglomerationEncoder
from tests.unit.executors.encoders.numeric import NumericTestCase


class FeatureAgglomerationEncoderTestCase(NumericTestCase):
    def _get_encoder(self):
        self.input_dim = 28
        self.target_output_dim = 2
        encoder = FeatureAgglomerationEncoder(output_dim=self.target_output_dim)
        return encoder
