__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import re
from typing import List, Dict

from .. import BaseSegmenter


class Sentencizer(BaseSegmenter):
    """
    :class:`Sentencizer` split the text on the doc-level into sentences on the chunk-level with a rule-base strategy.
    """

    def __init__(self,
                 min_sent_len: int = 1,
                 max_sent_len: int = -1,
                 punct_chars: str = None,
                 *args, **kwargs):
        """

        :param min_sent_len: the minimal length of the sentence.
        :param max_sent_len: the maximal length of the sentence.
        :param punct_chars: the punctuation characters to split on.
        """
        super().__init__(*args, **kwargs)
        self.min_sent_len = min_sent_len
        self.max_sent_len = max_sent_len if max_sent_len > 0 else 1e5
        self.punct_chars = punct_chars
        if not punct_chars:
            self.punct_chars = ['!', '.', '?', '։', '؟', '۔', '܀', '܁', '܂', '‼', '‽', '⁇', '⁈', '⁉', '⸮', '﹖', '﹗',
                                '！', '．', '？', '｡', '。']
        self._slit_pat = re.compile('([{0}])+([^{0}])'.format(''.join(self.punct_chars)))

    def craft(self, raw_bytes: bytes, doc_id: int, *args, **kwargs) -> List[Dict]:
        """
        Split the text into sentences.

        :param raw_bytes: the raw text in the `bytes` format
        :param doc_id: the doc id
        :return: a list of chunk dicts with the cropped images
        """
        text = raw_bytes.decode('utf8')
        sents_str = self._slit_pat.sub(r'\n\2', '{}\n'.format(text))
        sents_str = sents_str.rstrip('\n')
        sents = [s.strip() for s in sents_str.split('\n') if self.min_sent_len <= len(s.strip()) <= self.max_sent_len]
        results = []
        for idx, s in enumerate(sents):
            results.append(
                dict(doc_id=doc_id, text=s, offset=idx, weight=1.0, length=len(sents)))
        return results

class JiebaSegmenter(BaseSegmenter):
    """
    :class:`JiebaSegmenter` split the chinese text on the doc-level into words on the chunk-level with `jieba`.
    """

    def __init__(self, mode: str='accurate', *args, **kwargs):
        """

        :param mode: the jieba cut mode, accurate, all, search. default accurate
        """
        super().__init__(*args, **kwargs)
        if mode not in ('accurate', 'all', 'search'):
            raise ValueError('you must choose one of modes to cut the text: accurate, all, search.')
        self.mode = mode

    def craft(self, raw_bytes: bytes, doc_id: int, *args, **kwargs) -> List[Dict]:
        """
        Split the chinese text into words
        :param raw_bytes: the raw text in the `bytes` format
        :param doc_id: the doc id
        :return: a list of chunk dicts
        """
        import jieba
        text = raw_bytes.decode('utf-8')
        if self.mode == 'search':
            words = jieba.cut_for_search(text)
        elif self.mode == 'all':
            words = jieba.cut(text, cut_all=True)
        else:
            words = jieba.cut(text)

        chunks = []
        for idx, word in enumerate(words):
            chunks.append(
                dict(doc_id=doc_id, text=word, offset=idx, weight=1.0, length=len(word)))

        return chunks