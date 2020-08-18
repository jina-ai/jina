from jina.hub.encoders.nlp.use import UniversalSentenceEncoder
from tests.unit.executors.encoders.nlp import NlpTestCase


class UniversalSentenceEncoderTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return UniversalSentenceEncoder(metas=metas)
