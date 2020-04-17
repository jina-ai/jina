import unittest

from jina.executors.encoders.nlp.transformer import TransformerTFEncoder, TransformerTorchEncoder
from . import NlpTestCase


class PytorchTestCase(NlpTestCase):
    def _get_encoder(self):
        encoder = TransformerTorchEncoder(model_name='bert-base-uncased', pooling_strategy='cls')
        return encoder


class TfTestCase(NlpTestCase):
    def _get_encoder(self):
        encoder = TransformerTFEncoder(model_name='bert-base-uncased', pooling_strategy='cls')
        return encoder


if __name__ == '__main__':
    unittest.main()
