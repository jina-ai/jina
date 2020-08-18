from jina.hub.encoders.nlp.flair import FlairTextEncoder
from tests.unit.executors.encoders.nlp import NlpTestCase


class FlairTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return FlairTextEncoder(embeddings=('word:glove',), pooling_strategy='mean', metas=metas)
