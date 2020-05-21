import mimetypes

from . import BaseDocCrafter


class DataURICrafter(BaseDocCrafter):
    def __init__(self, mimetype: str, charset: str = 'utf-8', base64: bool = False, *args,
                 **kwargs):
        """ Build MIME type document from binary raw_bytes. It takes binary input and converts it to MIME-specific data URI.

        :param mimetype: media type defined in https://en.wikipedia.org/wiki/Media_type you can also give a file extension
                        only and let it guess the mimetype
        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit. Designed to be efficient for non-text 8 bit and binary data. Sometimes used for text data that frequently uses non-US-ASCII characters.
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.mimetype = None
        if mimetype in mimetypes.types_map.values():
            self.mimetype = mimetype
        if not self.mimetype:
            self.mimetype = mimetypes.guess_type(f'*.{mimetype}')[0]
        if not self.mimetype:
            raise NotImplementedError(f'i can not determine the MIME type from '
                                      f'mimetype={mimetype}, please check your input')

        self.charset = charset
        self.base64 = base64

    def craft(self, raw_bytes, *args, **kwargs):
        parts = ['data:', self.mimetype]
        if self.charset is not None:
            parts.extend([';charset=', self.charset])
        if self.base64:
            parts.append(';base64')
            from base64 import encodebytes as encode64
            encoded_data = encode64(raw_bytes).decode(self.charset).replace('\n', '').strip()
        else:
            from urllib.parse import quote_from_bytes
            encoded_data = quote_from_bytes(raw_bytes)
        parts.extend([',', encoded_data])
        return dict(data_uri=''.join(parts))
