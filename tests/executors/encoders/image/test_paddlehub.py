import unittest

from jina.executors.encoders.image.paddlehub import ImagePaddlehubEncoder
from . import ImageTestCase
from jina.executors.metas import get_default_metas


class MyTestCase(ImageTestCase):
    def _get_encoder(self):
        self.target_output_dim = 2048
        self.input_dim = 224
        metas = get_default_metas()
        metas['on_gpu'] = True
        return ImagePaddlehubEncoder(metas=metas)


if __name__ == '__main__':
    unittest.main()
