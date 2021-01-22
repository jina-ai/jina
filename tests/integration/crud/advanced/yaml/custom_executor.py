import re
import string
from typing import Dict, List

from jina.executors.rankers import Chunk2DocRanker
from jina.executors.segmenters import BaseSegmenter


class DummySentencizer(BaseSegmenter):

    def __init__(self,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        punct_chars = [',']
        self._slit_pat = re.compile('\s*([^{0}]+)(?<!\s)[{0}]*'.format(''.join(set(punct_chars))))

    def segment(self, text: str, *args, **kwargs) -> List[Dict]:
        """
        Split the text into sentences.

        :param text: the raw text
        :return: a list of chunks
        """
        results = []
        ret = [(m.group(0), m.start(), m.end()) for m in
               re.finditer(self._slit_pat, text)]
        if not ret:
            ret = [(text, 0, len(text))]
        for ci, (r, s, e) in enumerate(ret):
            f = ''.join(filter(lambda x: x in string.printable, r))
            f = re.sub('\n+', ' ', f).strip()
            f = f[:100]
            results.append(dict(
                text=f
            ))
        return results

class DummyRanker(Chunk2DocRanker):
    """
    :class:`MinRanker` calculates the score of the matched doc from the matched chunks. For each matched doc, the score
        is `1 / (1 + s)`, where `s` is the minimal score from all the matched chunks belonging to this doc.

    .. warning:: Here we suppose that the smaller chunk score means the more similar.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        import warnings
        warnings.warn("MinRanker is deprecated. Please use SimpleAggregateRanker instead", DeprecationWarning,
                      stacklevel=2)

    def _get_score(self, match_idx, query_chunk_meta, match_chunk_meta, *args, **kwargs):
        return self.get_doc_id(match_idx), 1. / (1. + match_idx[self.COL_SCORE].min())
