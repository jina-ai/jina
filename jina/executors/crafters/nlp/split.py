import re
import json
import string
from typing import List, Dict

from .. import BaseSegmenter


class Sentencizer(BaseSegmenter):
    def __init__(self,
                 min_sent_len: int = 1,
                 max_sent_len: int = -1,
                 punct_chars: str = None,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.min_sent_len = min_sent_len
        self.max_sent_len = max_sent_len if max_sent_len > 0 else 1e5
        self.punct_chars = punct_chars
        if not punct_chars:
            self.punct_chars = ['!', '.', '?', '։', '؟', '۔', '܀', '܁', '܂', '‼', '‽', '⁇', '⁈', '⁉', '⸮', '﹖', '﹗',
                                '！', '．', '？', '｡', '。']
        self._slit_pat = re.compile('([{0}])+([^{0}])'.format(''.join(self.punct_chars)))

    def craft(self, raw_bytes: bytes, doc_id: int, *args, **kwargs) -> List[Dict]:
        text = raw_bytes.decode('utf8')
        # split into sentences
        sents_str = self._slit_pat.sub(r'\1\n\2', text)
        sents_str = sents_str.rstrip('\n')
        sents = [s for s in sents_str.split('\n') if self.min_sent_len <= len(s) <= self.max_sent_len]
        results = []
        for idx, s in enumerate(sents):
            results.append(
                dict(doc_id=doc_id, text=s, offset=idx, weight=1.0, length=len(sents)))
        return results
