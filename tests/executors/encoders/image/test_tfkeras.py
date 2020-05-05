import unittest

from jina.executors.encoders.image.tfkeras import KerasImageEncoder
from . import ImageTestCase


class MyTestCase(ImageTestCase):
    def _get_encoder(self):
        self.target_output_dim = 1280
        self.input_dim = 224
        return KerasImageEncoder(channel_axis=1)


if __name__ == '__main__':
    unittest.main()
