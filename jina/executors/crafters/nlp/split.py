__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import re
from typing import List, Dict

from .. import BaseSegmenter


class Sentencizer(BaseSegmenter):
    """
    :class:`Sentencizer` split the text on the doc-level into sentences on the chunk-level with a rule-base strategy.
        The text is split by the punctuation characters listed in ``punct_chars``.
        The sentences that are shorter than the ``min_sent_len`` or longer than the ``max_sent_len`` after stripping will be discarded.
    """

    def __init__(self,
                 min_sent_len: int = 1,
                 max_sent_len: int = 1e5,
                 punct_chars: str = None,
                 *args, **kwargs):
        """

        :param min_sent_len: the minimal number of characters (including white spaces) of the sentence, by default 1.
        :param max_sent_len: the maximal number of characters (including white spaces) of the sentence, by default 1e5.
        :param punct_chars: the punctuation characters to split on.
        """
        super().__init__(*args, **kwargs)
        self.min_sent_len = min_sent_len
        self.max_sent_len = max_sent_len
        self.punct_chars = punct_chars
        if not punct_chars:
            self.punct_chars = ['!', '.', '?', '։', '؟', '۔', '܀', '܁', '܂', '‼', '‽', '⁇', '⁈', '⁉', '⸮', '﹖', '﹗',
                                '！', '．', '？', '｡', '。', '\n']
        if self.min_sent_len > self.max_sent_len:
            self.logger.warning('the min_sent_len (={}) should be smaller or equal to the max_sent_len (={})'.format(
                self.min_sent_len, self.max_sent_len))
        self._slit_pat = re.compile('\s*([^{0}]+)(?<!\s)[{0}]*'.format(''.join(self.punct_chars)))

    def craft(self, buffer: bytes, doc_id: int, *args, **kwargs) -> List[Dict]:
        """
        Split the text into sentences.

        :param buffer: the raw text in the `bytes` format
        :param doc_id: the doc id
        :return: a list of chunk dicts with the cropped images
        """

        text = buffer.decode('utf8')
        all_sentences = self._slit_pat.findall(text)
        results = []
        for idx, s in enumerate(all_sentences):
            if self.min_sent_len <= len(s) <= self.max_sent_len:
                results.append(dict(
                    doc_id=doc_id,
                    text=s,
                    offset=idx,
                    weight=1.0,
                    length=len(all_sentences)))
        return results


class JiebaSegmenter(BaseSegmenter):
    """
    :class:`JiebaSegmenter` split the chinese text on the doc-level into words on the chunk-level with `jieba`.
    """

    def __init__(self, mode: str = 'accurate', *args, **kwargs):
        """

        :param mode: the jieba cut mode, accurate, all, search. default accurate
        """
        super().__init__(*args, **kwargs)
        if mode not in ('accurate', 'all', 'search'):
            raise ValueError('you must choose one of modes to cut the text: accurate, all, search.')
        self.mode = mode

    def craft(self, buffer: bytes, doc_id: int, *args, **kwargs) -> List[Dict]:
        """
        Split the chinese text into words
        :param buffer: the raw text in the `bytes` format
        :param doc_id: the doc id
        :return: a list of chunk dicts
        """
        import jieba
        text = buffer.decode('utf-8')
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
