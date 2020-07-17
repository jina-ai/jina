import unittest

from jina.executors.encoders.image.paddlehub import ImagePaddlehubEncoder
from tests.unit.executors.encoders.image import ImageTestCase


class MyTestCase(ImageTestCase):
    def _get_encoder(self, metas):
        self.target_output_dim = 2048
        self.input_dim = 224
        return ImagePaddlehubEncoder(metas=metas)


if __name__ == '__main__':
    unittest.main()
