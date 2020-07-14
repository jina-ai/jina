import unittest

from jina.executors.encoders.image.bigtransfer import BiTImageEncoder
from tests.unit.executors.encoders.image import ImageTestCase


class MyTestCase(ImageTestCase):
    def _get_encoder(self, metas):
        self.target_output_dim = 8192
        self.input_dim = 48
        return BiTImageEncoder(
            model_path='/tmp/bit_models/Imagenet21k/R152x4/feature_vectors', channel_axis=1, metas=metas)


if __name__ == '__main__':
    unittest.main()
