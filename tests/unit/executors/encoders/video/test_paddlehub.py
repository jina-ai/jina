from jina.executors.encoders.video.paddlehub import VideoPaddlehubEncoder
from tests.unit.executors.encoders.video import VideoTestCase


class VideoPaddleHubTestCase(VideoTestCase):
    def _get_encoder(self, metas):
        self.target_output_dim = 2048
        self.input_dim = 224
        return VideoPaddlehubEncoder(metas=metas)
