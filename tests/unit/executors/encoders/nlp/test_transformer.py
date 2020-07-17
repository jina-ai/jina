import unittest

from jina.executors.encoders.nlp.transformer import TransformerTFEncoder, TransformerTorchEncoder
from tests.unit.executors.encoders.nlp import NlpTestCase


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


class XLNetPytorchTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return TransformerTorchEncoder(
            model_name='xlnet-base-cased',
            pooling_strategy='cls',
            metas=metas)


class XLNetTFTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return TransformerTFEncoder(
            model_name='xlnet-base-cased',
            pooling_strategy='cls',
            metas=metas)


if __name__ == '__main__':
    unittest.main()
