__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numpy as np

from .. import BaseTextEncoder
from ...decorators import batching, as_ndarray


class OneHotTextEncoder(BaseTextEncoder):
    """

    One-hot Encoder encodes the characters into one-hot vectors. ONLY FOR TESTING USAGES.
    :param on_value: the default value for the locations represented by characters
    :param off_value: the default value for the locations not represented by characters
    """

    def __init__(self,
                 on_value: float = 1,
                 off_value: float = 0,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.offset = 32
        self.dim = 127 - self.offset + 2  # only the Unicode code point between 32 and 127 are embedded, and the rest are considered as ``UNK```
        self.unk = self.dim
        self.on_value = on_value
        self.off_value = off_value
        self.embeddings = None

    def post_init(self):
        self.embeddings = np.eye(self.dim) * self.on_value + \
                          (np.ones((self.dim, self.dim)) - np.eye(self.dim)) * self.off_value

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: each row is one character, an 1d array of string type (data.dtype.kind == 'U') in size B
        :return: an ndarray of `B x D`
        """
        output = []
        for r in data:
            r_emb = [ord(c) - self.offset if self.offset <= ord(c) <= 127 else self.unk for c in r]
            output.append(self.embeddings[r_emb, :].sum(axis=0))
        return np.array(output)
