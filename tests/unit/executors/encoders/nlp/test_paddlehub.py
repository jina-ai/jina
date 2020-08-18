import os

from jina.hub.encoders.nlp.paddlehub import TextPaddlehubEncoder
from tests.unit.executors.encoders.nlp import NlpTestCase


class PaddleHubTestCase(NlpTestCase):
    def _get_encoder(self, metas):
        return TextPaddlehubEncoder(
            max_length=10, workspace=os.environ['TEST_WORKDIR'], metas=metas)
