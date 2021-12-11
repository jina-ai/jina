from collections import Counter
from typing import Tuple, Dict, Union, Optional

import numpy as np

from .helper import _uri_to_buffer, _to_datauri
from ...helper import T, deprecate_by


class TextDataMixin:
    """Provide helper functions for :class:`Document` to support text data. """

    def load_uri_to_text(self: T, charset: str = 'utf-8') -> T:
        """Convert :attr:`.uri` to :attr`.text` inplace.

        :param charset: charset may be any character set registered with IANA
        :return: itself after processed
        """
        buffer = _uri_to_buffer(self.uri)
        self.text = buffer.decode(charset)
        return self

    def get_vocabulary(self, text_attrs: Tuple[str, ...] = ('text',)) -> Dict[str, int]:
        """Get the text vocabulary in a counter dict that maps from the word to its frequency from all :attr:`text_fields`.

        :param text_attrs: the textual attributes where vocabulary will be derived from
        :return: a vocabulary in dictionary where key is the word, value is the frequency of that word in all text fields.
        """
        all_tokens = Counter()

        for f in text_attrs:
            all_tokens.update(_text_to_word_sequence(getattr(self, f)))

        return all_tokens

    def convert_text_to_blob(
        self: T,
        vocab: Dict[str, int],
        max_length: Optional[int] = None,
        dtype: str = 'int64',
    ) -> T:
        """Convert :attr:`.text` to :attr:`.blob` inplace.

        In the end :attr:`.blob` will be a 1D array where `D` is `max_length`.

        To get the vocab of a DocumentArray, you can use `jina.types.document.converters.build_vocab` to

        :param vocab: a dictionary that maps a word to an integer index, `0` is reserved for padding, `1` is reserved
            for unknown words in :attr:`.text`. So you should *not* include these two entries in `vocab`.
        :param max_length: the maximum length of the sequence. Sequence longer than this are cut off from *beginning*.
            Sequence shorter than this will be padded with `0` from right hand side.
        :param dtype: the dtype of the generated :attr:`.blob`
        :return: Document itself after processed
        """
        self.blob = np.array(
            _text_to_int_sequence(self.text, vocab, max_length), dtype=dtype
        )
        return self

    def convert_blob_to_text(
        self: T, vocab: Union[Dict[str, int], Dict[int, str]], delimiter: str = ' '
    ) -> T:
        """Convert :attr:`.blob` to :attr:`.text` inplace.

        :param vocab: a dictionary that maps a word to an integer index, `0` is reserved for padding, `1` is reserved
            for unknown words in :attr:`.text`
        :param delimiter: the delimiter that used to connect all words into :attr:`.text`
        :return: Document itself after processed
        """
        if isinstance(list(vocab.keys())[0], str):
            _vocab = {v: k for k, v in vocab.items()}

        _text = []
        for k in self.blob:
            k = int(k)
            if k == 0:
                continue
            elif k == 1:
                _text.append('<UNK>')
            else:
                _text.append(_vocab.get(k, '<UNK>'))
        self.text = delimiter.join(_text)
        return self

    def dump_text_to_datauri(
        self: T, charset: str = 'utf-8', base64: bool = False
    ) -> T:
        """Convert :attr:`.text` to data :attr:`.uri`.

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit.
            Designed to be efficient for non-text 8 bit and binary data.
            Sometimes used for text data that frequently uses non-US-ASCII characters.

        :return: itself after processed
        """

        self.uri = _to_datauri(self.mime_type, self.text, charset, base64, binary=False)
        return self

    convert_uri_to_text = deprecate_by(load_uri_to_text)
    convert_text_to_uri = deprecate_by(dump_text_to_datauri)


def _text_to_word_sequence(
    text, filters='!"#$%&()*+,-./:;<=>?@[\\]^_`{|}~\t\n', split=' '
):
    translate_dict = {c: split for c in filters}
    translate_map = str.maketrans(translate_dict)
    text = text.lower().translate(translate_map)

    seq = text.split(split)
    for i in seq:
        if i:
            yield i


def _text_to_int_sequence(text, vocab, max_len=None):
    seq = _text_to_word_sequence(text)
    vec = [vocab.get(s, 1) for s in seq]
    if max_len:
        if len(vec) < max_len:
            vec = [0] * (max_len - len(vec)) + vec
        elif len(vec) > max_len:
            vec = vec[-max_len:]
    return vec
