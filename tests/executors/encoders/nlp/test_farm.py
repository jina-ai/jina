import unittest

from jina.executors.encoders.nlp.farm import FarmTextEncoder
from . import NlpTestCase


class MyTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return FarmTextEncoder(metas=metas)


if __name__ == '__main__':
    unittest.main()
