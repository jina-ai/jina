import unittest

from jina.executors.encoders.nlp.transformer import TransformerTFEncoder, TransformerTorchEncoder
from . import NlpTestCase


class PytorchTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return TransformerTorchEncoder(
            model_name='bert-base-uncased',
            pooling_strategy='cls',
            metas=metas)


class TfTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return TransformerTFEncoder(
            model_name='bert-base-uncased',
            pooling_strategy='cls',
            metas=metas)


if __name__ == '__main__':
    unittest.main()
