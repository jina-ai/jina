__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import base64
import os
import struct
import urllib.parse
import urllib.request
import zlib

import numpy as np

from . import BaseDocCrafter


class URI2Buffer(BaseDocCrafter):
    """ Convert local file path, remote URL doc to a buffer doc.
    """

    def craft(self, uri: str, *args, **kwargs):
        if urllib.parse.urlparse(uri).scheme in {'http', 'https', 'data'}:
            page = urllib.request.Request(uri, headers={'User-Agent': 'Mozilla/5.0'})
            tmp = urllib.request.urlopen(page)
            buffer = tmp.read()
        elif os.path.exists(uri):
            with open(uri, 'rb') as fp:
                buffer = fp.read()
        else:
            raise FileNotFoundError(f'{uri} is not a URL or a valid local path')
        return dict(buffer=buffer)


class Path2DataURI(URI2Buffer):
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

    def craft(self, uri: str, mime_type: str, *args, **kwargs):
        d = super().craft(uri)
        return dict(uri=self.make_datauri(mime_type, d['buffer']))

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


class Buffer2DataURI(Path2DataURI):
    """Convert buffer to data URI"""

    def craft(self, buffer: bytes, mime_type: str, *args, **kwargs):
        return dict(uri=self.make_datauri(mime_type, buffer))


class Buffer2NdArray(BaseDocCrafter):
    """Convert buffer to numpy array"""

    def craft(self, buffer: bytes, *args, **kwargs):
        return dict(blob=np.frombuffer(buffer))


class Blob2PNGDataURI(BaseDocCrafter):
    """Simple DocCrafter used in :command:`jina hello-world`,
        it reads ``buffer`` into base64 png and stored in ``uri``"""

    def __init__(self, width: int = 28, height: int = 28, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.width = width
        self.height = height

    def craft(self, blob, *args, **kwargs):
        pixels = []
        for p in blob[::-1]:
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
        return dict(uri='data:image/png;base64,' + base64.b64encode(png_bytes).decode())
