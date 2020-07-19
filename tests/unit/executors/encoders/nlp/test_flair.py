import unittest

from jina.executors.encoders.nlp.flair import FlairTextEncoder
from tests.unit.executors.encoders.nlp import NlpTestCase


class MyTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return FlairTextEncoder(embeddings=('word:glove',), pooling_strategy='mean', metas=metas)


if __name__ == '__main__':
    unittest.main()
