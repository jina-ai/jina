__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
import urllib.parse
import urllib.request

from . import BaseDocCrafter


class FilePath2Buffer(BaseDocCrafter):
    """ Convert local file path, remote URL doc to a buffer doc.
    """

    def craft(self, file_path: str, *args, **kwargs):
        if urllib.parse.urlparse(file_path).scheme in {'http', 'https', 'data'}:
            page = urllib.request.Request(file_path, headers={'User-Agent': 'Mozilla/5.0'})
            tmp = urllib.request.urlopen(page)
            buffer = tmp.read()
        elif os.path.exists(file_path):
            with open(file_path, 'rb') as fp:
                buffer = fp.read()
        else:
            raise FileNotFoundError(f'{file_path} is not a URL or a valid local path')
        return dict(buffer=buffer)


class DataURI2Buffer(FilePath2Buffer):
    """ Convert a data URI doc to a buffer doc.
    """

    def craft(self, data_uri: str, *args, **kwargs):
        return super().craft(data_uri)


class Any2Buffer(DataURI2Buffer):
    def craft(self, file_path: str, data_uri: str, buffer: bytes, *args, **kwargs):
        if buffer:
            pass
        elif file_path:
            return super(FilePath2Buffer, self).craft(file_path)
        elif data_uri:
            return super(DataURI2Buffer, self).craft(data_uri)
        else:
            raise ValueError('this document has no "file_path", no "data_uri" and no "buffer" set')


class FilePath2DataURI(FilePath2Buffer):
    def __init__(self, charset: str = 'utf-8', base64: bool = False, *args, **kwargs):
        """ Convert file path doc to data uri doc.

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit. Designed to be efficient for non-text 8 bit and binary data. Sometimes used for text data that frequently uses non-US-ASCII characters.
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.charset = charset
        self.base64 = base64

    def craft(self, file_path: str, mime_type: str, *args, **kwargs):
        d = super().craft(file_path)
        return dict(data_uri=self.make_datauri(mime_type, d['buffer']))

    def make_datauri(self, mimetype, buffer):
        parts = ['data:', mimetype]
        if self.charset is not None:
            parts.extend([';charset=', self.charset])
        if self.base64:
            parts.append(';base64')
            from base64 import encodebytes as encode64
            encoded_data = encode64(buffer).decode(self.charset).replace('\n', '').strip()
        else:
            from urllib.parse import quote_from_bytes
            encoded_data = quote_from_bytes(buffer)
        parts.extend([',', encoded_data])
        return ''.join(parts)


class Buffer2DataURI(FilePath2DataURI):

    def craft(self, buffer: bytes, mime_type: str, *args, **kwargs):
        return dict(data_uri=self.make_datauri(mime_type, buffer))
