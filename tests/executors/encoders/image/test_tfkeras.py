import unittest

from jina.executors.encoders.image.tfkeras import KerasImageEncoder
from . import ImageTestCase


class MyTestCase(ImageTestCase):
    def get_encoder(self, model_path=None):
        self.target_output_dim = 1280
        return KerasImageEncoder(channel_axis=1)


if __name__ == '__main__':
    unittest.main()
