__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import mimetypes

from . import BaseDocCrafter


class File2DataURICrafter(BaseDocCrafter):
    def __init__(self, charset: str = 'utf-8', base64: bool = False, *args, **kwargs):
        """ Build MIME type document from file name. The MIME type is guessed from the file name extension

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit. Designed to be efficient for non-text 8 bit and binary data. Sometimes used for text data that frequently uses non-US-ASCII characters.
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.charset = charset
        self.base64 = base64

    def craft(self, raw_bytes, *args, **kwargs):
        p = raw_bytes.decode()
        mimetype, _ = mimetypes.guess_type(p)
        if not mimetype:
            self.logger.warning(f'can not determine the '
                                f'media type from the filename and extension of {p}, '
                                f'the result data URI may not be readable')
            mimetype = ''
        with open(p, 'rb') as fp:
            raw_bytes = fp.read()

        return dict(data_uri=self.make_datauri(mimetype, raw_bytes))

    def make_datauri(self, mimetype, raw_bytes):
        parts = ['data:', mimetype]
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
        return ''.join(parts)


class Bin2DataURICrafter(File2DataURICrafter):
    def __init__(self, mimetype: str, *args,
                 **kwargs):
        """ Build MIME type document from binary raw_bytes.
        It takes binary input and converts it to MIME-specific data URI. Therefore :attr:`mimetype` must be given.

        :param mimetype: media type defined in https://en.wikipedia.org/wiki/Media_type you can also give a file extension
                        only and let it guess the mimetype
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

    def craft(self, raw_bytes, *args, **kwargs):
        return dict(data_uri=self.make_datauri(self.mimetype, raw_bytes))
