import unittest

from jina.executors.encoders.image.torchvision import ImageTorchEncoder
from . import ImageTestCase


class MyTestCase(ImageTestCase):
    def _get_encoder(self):
        self.target_output_dim = 1280
        return ImageTorchEncoder()


if __name__ == '__main__':
    unittest.main()
