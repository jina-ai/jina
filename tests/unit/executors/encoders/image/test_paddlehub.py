from jina.hub.encoders.image.paddlehub import ImagePaddlehubEncoder
from tests.unit.executors.encoders.image import ImageTestCase


class PaddleHubTestCase(ImageTestCase):
    def _get_encoder(self, metas):
        self.target_output_dim = 2048
        self.input_dim = 224
        return ImagePaddlehubEncoder(metas=metas)
