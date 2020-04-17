import os
import unittest

from jina.executors.encoders.nlp.paddlehub import TextPaddlehubEncoder
from . import NlpTestCase


class MyTestCase(NlpTestCase):
    def _get_encoder(self):
        return TextPaddlehubEncoder(max_length=10, workspace=os.environ['TEST_WORKDIR'])


if __name__ == '__main__':
    unittest.main()
