import unittest

from jina.executors.encoders.image.paddlehub import ImagePaddlehubEncoder
from . import ImageTestCase


class MyTestCase(ImageTestCase):
    def get_encoder(self, model_path=None):
        self.target_output_dim = 2048
        return ImagePaddlehubEncoder()


if __name__ == '__main__':
    unittest.main()
