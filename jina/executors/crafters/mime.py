__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import mimetypes

from . import BaseDocCrafter


class FilePath2Bytes(BaseDocCrafter):
    def craft(self, file_path, *args, **kwargs):
        with open(file_path, 'rb') as fp:
            buffer = fp.read()
        mimetype = mimetypes.guess_type(file_path)[0]
        return dict(buffer=buffer, mime_type=mimetype)


class FilePath2DataURI(BaseDocCrafter):
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

    def craft(self, file_path, *args, **kwargs):
        mimetype, _ = mimetypes.guess_type(file_path)
        if not mimetype:
            self.logger.warning(f'can not determine the '
                                f'media type from the filename and extension of {p}, '
                                f'the result data URI may not be readable')
            mimetype = 'application/octet-stream'  # default by IANA standard
        with open(file_path, 'rb') as fp:
            buffer = fp.read()

        return dict(data_uri=self.make_datauri(mimetype, buffer),
                    mime_type=mimetype)

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


class Bytes2DataURI(FilePath2DataURI):
    def __init__(self, mimetype: str = None, *args,
                 **kwargs):
        """ Build MIME type document from binary buffer.
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
            self.logger.warning(f'i can not determine the MIME type from '
                                f'mimetype={mimetype}, I will do MIME sniffing on-the-fly. '
                                f'MIME sniffing requires pip install "jina[http]" '
                                f'and brew install libmagic (Mac)/ apt-get install libmagic1 (Linux)')

    def craft(self, buffer, mime_type, *args, **kwargs):
        if self.mimetype:
            m_type = self.mimetype
        elif mime_type:
            m_type = mime_type
        else:
            import magic
            m_type = magic.from_buffer(buffer, mime=True)
        return dict(data_uri=self.make_datauri(self.mimetype, buffer),
                    mime_type=m_type)


class DataURI2Bytes(BaseDocCrafter):
    """Convert data URI to buffer at the doc level """

    def craft(self, data_uri: str, *args, **kwargs):
        import urllib.request
        if data_uri.startswith('data:'):
            tmp = urllib.request.urlopen(data_uri)
            mimetype = tmp.info().get_content_type()
            buffer = tmp.file.read()
            return dict(buffer=buffer, mime_type=mimetype)
        else:
            self.logger.error(f'expecting data URI, but got {data_uri}')
