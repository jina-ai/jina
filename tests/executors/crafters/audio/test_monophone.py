import unittest

import numpy as np
from jina.executors.crafters.audio.monophone import AudioMonophoner
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    def test_mono(self):
        signal_orig = np.random.randn(2, 31337)

        crafter = AudioMonophoner()
        crafted_doc = crafter.craft(signal_orig, 0)

        signal_mono = crafted_doc["blob"]
        self.assertEqual(signal_mono.shape[0], signal_orig.shape[1])


if __name__ == '__main__':
    unittest.main()
