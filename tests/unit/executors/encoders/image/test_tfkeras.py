from jina.hub.encoders.image.keras import KerasImageEncoder
from tests.unit.executors.encoders.image import ImageTestCase


class KerasTestCase(ImageTestCase):
    def _get_encoder(self, metas):
        self.target_output_dim = 1280
        self.input_dim = 96
        return KerasImageEncoder(channel_axis=1, metas=metas)
