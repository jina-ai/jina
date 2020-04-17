import unittest

from jina.executors.encoders.video.paddlehub import VideoPaddlehubEncoder
from . import VideoTestCase


class MyTestCase(VideoTestCase):
    def _get_encoder(self):
        self.target_output_dim = 2048
        self.input_dim = 224
        return VideoPaddlehubEncoder()


if __name__ == '__main__':
    unittest.main()
