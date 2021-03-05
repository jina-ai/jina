import re
import string
from typing import Dict, List

from jina.executors.decorators import batching, as_ndarray
from jina.executors.encoders import BaseTextEncoder
from jina.executors.rankers import Chunk2DocRanker
from jina.executors.segmenters import BaseSegmenter
import numpy as np


class DummySentencizer(BaseSegmenter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        punct_chars = [',']
        self._slit_pat = re.compile(
            '\s*([^{0}]+)(?<!\s)[{0}]*'.format(''.join(set(punct_chars)))
        )

    def segment(self, text: str, *args, **kwargs) -> List[Dict]:
        """
        Split the text into sentences.

        :param text: the raw text
        :return: a list of chunks
        """
        results = []
        ret = [
            (m.group(0), m.start(), m.end()) for m in re.finditer(self._slit_pat, text)
        ]
        if not ret:
            ret = [(text, 0, len(text))]
        for ci, (r, s, e) in enumerate(ret):
            f = ''.join(filter(lambda x: x in string.printable, r))
            f = re.sub('\n+', ' ', f).strip()
            f = f[:100]
            results.append(dict(text=f))
        return results


class DummyMinRanker(Chunk2DocRanker):
    """
    :class:`MinRanker` calculates the score of the matched doc from the matched chunks. For each matched doc, the score
        is `1 / (1 + s)`, where `s` is the minimal score from all the matched chunks belonging to this doc.

    .. warning:: Here we suppose that the smaller chunk score means the more similar.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import warnings

        warnings.warn(
            "MinRanker is deprecated. Please use SimpleAggregateRanker instead",
            DeprecationWarning,
            stacklevel=2,
        )

    def _get_score(
        self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs
    ):
        return self.get_doc_id(match_idx), 1.0 / (1.0 + match_idx[self.COL_SCORE].min())


class DummyOneHotTextEncoder(BaseTextEncoder):
    """
    One-hot Encoder encodes the characters into one-hot vectors. ONLY FOR TESTING USAGES.
    :param on_value: the default value for the locations represented by characters
    :param off_value: the default value for the locations not represented by characters
    """

    def __init__(self, on_value: float = 1, off_value: float = 0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.offset = 32
        self.dim = (
            127 - self.offset + 2
        )  # only the Unicode code point between 32 and 127 are embedded, and the rest are considered as ``UNK```
        self.unk = self.dim
        self.on_value = on_value
        self.off_value = off_value
        self.embeddings = None

    def post_init(self):
        self.embeddings = (
            np.eye(self.dim) * self.on_value
            + (np.ones((self.dim, self.dim)) - np.eye(self.dim)) * self.off_value
        )

    @batching
    @as_ndarray
    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'np.ndarray':
        """

        :param data: each row is one character, an 1d array of string type (data.dtype.kind == 'U') in size B
        :return: an ndarray of `B x D`
        """
        output = []
        for r in data:
            r_emb = [
                ord(c) - self.offset if self.offset <= ord(c) <= 127 else self.unk
                for c in r
            ]
            output.append(self.embeddings[r_emb, :].sum(axis=0))
        return np.array(output)
