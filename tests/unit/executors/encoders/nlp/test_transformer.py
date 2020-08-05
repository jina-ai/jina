from jina.executors.encoders.nlp.transformer import TransformerTFEncoder, TransformerTorchEncoder
from tests.unit.executors.encoders.nlp import NlpTestCase


class PytorchTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return TransformerTorchEncoder(
            pretrained_model_name_or_path='bert-base-uncased',
            metas=metas)


class TfTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return TransformerTFEncoder(
            pretrained_model_name_or_path='bert-base-uncased',
            metas=metas)


class XLNetPytorchTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return TransformerTorchEncoder(
            pretrained_model_name_or_path='xlnet-base-cased',
            metas=metas)


class XLNetTFTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return TransformerTFEncoder(
            pretrained_model_name_or_path='xlnet-base-cased',
            metas=metas)
