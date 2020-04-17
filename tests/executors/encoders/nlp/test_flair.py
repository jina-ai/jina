import unittest

from jina.executors.encoders.nlp.flair import FlairTextEncoder
from . import NlpTestCase


class MyTestCase(NlpTestCase):
    def _get_encoder(self):
        return FlairTextEncoder(embeddings=('word:glove',), pooling_strategy='mean')


if __name__ == '__main__':
    unittest.main()
