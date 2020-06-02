__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import base64
import os
import struct
import urllib.parse
import urllib.request
import zlib

import numpy as np

from . import BaseDriver
from .helper import guess_mime, array2pb, pb2array


class BaseConvertDriver(BaseDriver):

    def __init__(self, override: bool = False, *args, **kwargs):
        """

        :param override: override the value even when exits
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.override = override


class MIMEDriver(BaseConvertDriver):
    """Guessing the MIME type based on the doc content

    Can be used before/after :class:`DocCraftDriver` to fill MIME type
    """

    def __init__(self, default_mime: str = 'application/octet-stream', *args, **kwargs):
        """

        :param default_mime: for text documents without a specific subtype, text/plain should be used.
            Similarly, for binary documents without a specific or known subtype, application/octet-stream should be used.
        """
        super().__init__(*args, **kwargs)
        self.default_mime = default_mime
        self.buffer_sniff = False
        try:
            import magic
            self.buffer_sniff = True
        except (ImportError, ModuleNotFoundError):
            self.logger.warning(f'can not sniff the MIME type '
                                f'MIME sniffing requires pip install "jina[http]" '
                                f'and brew install libmagic (Mac)/ apt-get install libmagic1 (Linux)')

    def __call__(self, *args, **kwargs):
        import mimetypes

        for d in self.req.docs:
            # mime_type may be a file extension
            m_type = d.mime_type

            if m_type and not self.override:
                continue

            if m_type and (m_type not in mimetypes.types_map.values()):
                m_type = mimetypes.guess_type(f'*.{m_type}')[0]

            if not m_type:  # for ClientInputType=PROTO, d_type could be empty
                d_type = d.WhichOneof('content')
                if d_type == 'buffer':
                    d_content = getattr(d, d_type)
                    if self.buffer_sniff:
                        try:
                            import magic
                            m_type = magic.from_buffer(d_content, mime=True)
                        except Exception as ex:
                            self.logger.warning(f'can not sniff the MIME type due to the exception {ex}')
                if d.uri:
                    m_type = guess_mime(d.uri)

            if m_type:
                d.mime_type = m_type
            else:
                d.mime_type = self.default_mime
                self.logger.warning(f'can not determine the MIME type, set to default {self.default_mime}')


class Buffer2NdArray(BaseConvertDriver):
    """Convert buffer to numpy array"""

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            if d.blob and not self.override:
                continue
            d.blob.CopyFrom(array2pb(np.frombuffer(d.buffer)))


class Blob2PngURI(BaseConvertDriver):
    """Simple DocCrafter used in :command:`jina hello-world`,
        it reads ``buffer`` into base64 png and stored in ``uri``"""

    def __init__(self, width: int = 28, height: int = 28, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.width = width
        self.height = height

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            if d.uri and not self.override:
                continue

            arr = pb2array(d.blob)
            pixels = []
            for p in arr[::-1]:
                pixels.extend([255 - int(p), 255 - int(p), 255 - int(p), 255])
            buf = bytearray(pixels)

            # reverse the vertical line order and add null bytes at the start
            width_byte_4 = self.width * 4
            raw_data = b''.join(
                b'\x00' + buf[span:span + width_byte_4]
                for span in range((self.height - 1) * width_byte_4, -1, - width_byte_4))

            def png_pack(png_tag, data):
                chunk_head = png_tag + data
                return (struct.pack('!I', len(data)) +
                        chunk_head +
                        struct.pack('!I', 0xFFFFFFFF & zlib.crc32(chunk_head)))

            png_bytes = b''.join([
                b'\x89PNG\r\n\x1a\n',
                png_pack(b'IHDR', struct.pack('!2I5B', self.width, self.height, 8, 6, 0, 0, 0)),
                png_pack(b'IDAT', zlib.compress(raw_data, 9)),
                png_pack(b'IEND', b'')])
            d.uri = 'data:image/png;base64,' + base64.b64encode(png_bytes).decode()


class URI2Buffer(BaseConvertDriver):
    """ Convert local file path, remote URL doc to a buffer doc.
    """

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:

            if d.buffer and not self.override:
                continue

            if urllib.parse.urlparse(d.uri).scheme in {'http', 'https', 'data'}:
                page = urllib.request.Request(d.uri, headers={'User-Agent': 'Mozilla/5.0'})
                tmp = urllib.request.urlopen(page)
                d.buffer = tmp.read()
            elif os.path.exists(d.uri):
                with open(d.uri, 'rb') as fp:
                    d.buffer = fp.read()
            else:
                raise FileNotFoundError(f'{d.uri} is not a URL or a valid local path')


class URI2DataURI(URI2Buffer):
    def __init__(self, charset: str = 'utf-8', base64: bool = False, *args, **kwargs):
        """ Convert file path doc to data uri doc. Internally it first reads into buffer and then converts it to data URI.

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit. Designed to be efficient for non-text 8 bit and binary data. Sometimes used for text data that frequently uses non-US-ASCII characters.
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.charset = charset
        self.base64 = base64

    def __call__(self, *args, **kwargs):
        super().__call__()
        for d in self.req.docs:
            if d.uri and not self.override:
                continue

            if d.uri and urllib.parse.urlparse(d.uri).scheme == 'data':
                pass
            else:
                d.uri = self.make_datauri(d.mime_type, d.buffer)

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


class Buffer2URI(URI2DataURI):
    """Convert buffer to data URI"""

    def __call__(self, *args, **kwargs):
        for d in self.req.docs:
            if d.uri and not self.override:
                continue

            if d.uri and urllib.parse.urlparse(d.uri).scheme == 'data':
                pass
            else:
                d.uri = self.make_datauri(d.mime_type, d.buffer)
