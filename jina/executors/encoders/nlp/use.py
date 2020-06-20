__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from ..frameworks import BaseTextTFEncoder
from ...decorators import batching, as_ndarray


class UniversalSentenceEncoder(BaseTextTFEncoder):
    """
    :class:`UniversalSentenceEncoder` is a encoder based on the Universal Sentence
    Encoder family (https://tfhub.dev/google/collections/universal-sentence-encoder/1).
    It encodes data from an 1d array of string in size `B` into an ndarray in size `B x D`.
    """

    def __init__(
            self,
            model_url: str = 'https://tfhub.dev/google/universal-sentence-encoder/4',
            *args,
            **kwargs):
        """
        :param model_url: the url of the model (TensorFlow Hub). For supported models see
                          family overview: https://tfhub.dev/google/collections/universal-sentence-encoder/1)
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        if self.model_url is None:
            self.model_url = 'https://tfhub.dev/google/universal-sentence-encoder/4'

    def post_init(self):
        self.to_device()
        import tensorflow_hub as hub
        self.model = hub.load(self.model_url)

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: a 1d array of string type in size `B`
        :param args:
        :param kwargs:
        :return: an ndarray in size `B x D`
        """
        return self.model(data).numpy()
