import unittest

from jina.executors.encoders.nlp.farm import FarmTextEncoder
from tests.unit.executors.encoders.nlp import NlpTestCase


class MyTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return FarmTextEncoder(metas=metas)


if __name__ == '__main__':
    unittest.main()
