import unittest

import numpy as np
from jina.executors.crafters.audio.normalize import AudioNormalizer
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    def test_norm(self):
        signal_orig = np.random.randn(2, 31337)

        crafter = AudioNormalizer()
        crafted_doc = crafter.craft(signal_orig, 0)

        signal_norm = crafted_doc["blob"]
        self.assertEqual(signal_norm.shape, signal_orig.shape)
        self.assertEqual(np.min(signal_norm), -1)
        self.assertEqual(np.max(signal_norm), 1)


if __name__ == '__main__':
    unittest.main()
