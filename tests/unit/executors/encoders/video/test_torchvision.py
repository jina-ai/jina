from jina.hub.encoders.video.torchvision import VideoTorchEncoder
from tests.unit.executors.encoders.video import VideoTestCase


class VideoTorchEncoderTestCase(VideoTestCase):
    def _get_encoder(self, metas):
        self.target_output_dim = 512
        self.input_dim = 112
        return VideoTorchEncoder(metas=metas)
