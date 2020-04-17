import unittest

from jina.executors.encoders.video.torchvision import VideoTorchEncoder
from . import VideoTestCase


class MyTestCase(VideoTestCase):
    def _get_encoder(self):
        self.target_output_dim = 512
        self.input_dim = 112
        return VideoTorchEncoder()


if __name__ == '__main__':
    unittest.main()
