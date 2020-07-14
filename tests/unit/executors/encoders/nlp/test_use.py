import unittest

from jina.executors.encoders.nlp.use import UniversalSentenceEncoder
from tests.unit.executors.encoders.nlp import NlpTestCase


class UniversalSentenceEncoderTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return UniversalSentenceEncoder(metas=metas)


if __name__ == '__main__':
    unittest.main()
