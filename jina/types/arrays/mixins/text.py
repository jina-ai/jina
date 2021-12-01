from collections import Counter
from typing import Tuple, Dict


class TextToolsMixin:
    """Help functions used in NLP for DA and DAM"""

    def get_vocabulary(
        self, min_freq: int = 1, text_attrs: Tuple[str, ...] = ('text',)
    ) -> Dict[str, int]:
        """Get the text vocabulary in a dict that maps from the word to the index from all Documents.

        :param text_attrs: the textual attributes where vocabulary will be derived from
        :param min_freq: the minimum word frequency to be considered into the vocabulary.
        :return: a vocabulary in dictionary where key is the word, value is the index. The value is 2-index, where
            `0` is reserved for padding, `1` is reserved for unknown token.
        """

        all_tokens = Counter()
        for d in self:
            all_tokens.update(d.get_vocabulary(text_attrs=text_attrs))

        # 0 for padding, 1 for unknown
        return {
            k: idx
            for idx, k in enumerate(
                (k for k, v in all_tokens.items() if v >= min_freq), start=2
            )
        }
