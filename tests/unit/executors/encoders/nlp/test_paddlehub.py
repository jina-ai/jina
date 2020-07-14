import os
import unittest

from jina.executors.encoders.nlp.paddlehub import TextPaddlehubEncoder
from tests.unit.executors.encoders.nlp import NlpTestCase


class MyTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return TextPaddlehubEncoder(
            max_length=10, workspace=os.environ['TEST_WORKDIR'], metas=metas)


if __name__ == '__main__':
    unittest.main()
