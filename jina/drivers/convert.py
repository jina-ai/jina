__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import base64
import os
import struct
import urllib.parse
import urllib.request
import zlib

import numpy as np

from typing import Iterable

from . import BaseRecursiveDriver
from .helper import guess_mime, array2pb, pb2array

if False:
    from ..proto import jina_pb2
    from PIL import Image

class BaseConvertDriver(BaseRecursiveDriver):

    def __init__(self, target: str, override: bool = False, *args, **kwargs):
        """ Set a target attribute of the document by another attribute

        :param target: attribute to set
        :param override: override the target value even when exits
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.override = override
        self.target = target

    def _apply_all(self, docs: Iterable['jina_pb2.Document'], *args, **kwargs):
        for doc in docs:
            if getattr(doc, self.target) and not self.override:
                pass
            else:
                self.convert(doc)

    def convert(self, d):
        raise NotImplementedError


class MIMEDriver(BaseConvertDriver):
    """Guessing the MIME type based on the doc content

    Can be used before/after :class:`DocCraftDriver` to fill MIME type
    """

    def __init__(self, target='mime', default_mime: str = 'application/octet-stream', *args, **kwargs):
        """

        :param default_mime: for text documents without a specific subtype, text/plain should be used.
            Similarly, for binary documents without a specific or known subtype, application/octet-stream should be used.
        """
        super().__init__(target, *args, **kwargs)
        self.default_mime = default_mime
        self.buffer_sniff = False
        try:
            import magic
            self.buffer_sniff = True
        except (ImportError, ModuleNotFoundError):
            self.logger.warning(f'can not sniff the MIME type '
                                f'MIME sniffing requires pip install "jina[http]" '
                                f'and brew install libmagic (Mac)/ apt-get install libmagic1 (Linux)')

    def convert(self, d):
        import mimetypes
        m_type = d.mime_type
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

    def __init__(self, target='blob', *args, **kwargs):
        super().__init__(target, *args, **kwargs)

    def convert(self, d):
        d.blob.CopyFrom(array2pb(np.frombuffer(d.buffer)))


class NdArray2PngURI(BaseConvertDriver):
    """Simple DocCrafter used in :command:`jina hello-world`,
        it reads ``NdArray`` into base64 png and stored in ``uri``"""

    def __init__(self, target='uri', width: int = 28, height: int = 28, resize_method: str = 'BILINEAR', *args, **kwargs):
        super().__init__(target, *args, **kwargs)
        self.width = width
        self.height = height
        self.resize_method = resize_method

    def png_convertor_1d(self, arr: np.array):
        pixels = []
        arr = 255 - arr
        for p in arr[::-1]:
            pixels.extend([p, p, p, 255])
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

        return 'data:image/png;base64,' + base64.b64encode(png_bytes).decode()

    @staticmethod
    def image_to_byte_array(image: 'Image', format: str):
        import io
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=format)
        img_byte_arr = img_byte_arr.getvalue()
        return img_byte_arr

    def png_convertor(self, arr: np.array):
        from PIL import Image

        arr = arr.astype(np.uint8)

        if len(arr.shape) == 1:
            return self.png_convertor_1d(arr)
        elif len(arr.shape) == 2:
            im = Image.fromarray(arr).convert('L')
            im = im.resize((self.width, self.height), getattr(Image, self.resize_method))
        elif len(arr.shape) == 3:
            im = Image.fromarray(arr).convert('RGB')
            im = im.resize((self.width, self.height), getattr(Image, self.resize_method))
        else:
            raise ValueError('arr shape length should be either 1, 2 or 3')

        png_bytes = NdArray2PngURI.image_to_byte_array(im, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(png_bytes).decode()
    
    def convert(self, arr: np.array):
        arr.uri = self.png_convertor(arr)


class Blob2PngURI(NdArray2PngURI):
    """Simple DocCrafter used in :command:`jina hello-world`,
        it reads ``buffer`` into base64 png and stored in ``uri``"""

    def __init__(self, target='uri', width: int = 28, height: int = 28, *args, **kwargs):
        super().__init__(target, width, height, *args, **kwargs)

    def convert(self, d):
        arr = pb2array(d.blob)
        d.uri = self.png_convertor(arr)


class URI2Buffer(BaseConvertDriver):
    """ Convert local file path, remote URL doc to a buffer doc.
    """

    def __init__(self, target='buffer', *args, **kwargs):
        super().__init__(target, *args, **kwargs)

    def convert(self, d):
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
    def __init__(self, target='uri', charset: str = 'utf-8', base64: bool = False, *args, **kwargs):
        """ Convert file path doc to data uri doc. Internally it first reads into buffer and then converts it to data URI.

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit. Designed to be efficient for non-text 8 bit and binary data. Sometimes used for text data that frequently uses non-US-ASCII characters.
        :param args:
        :param kwargs:
        """
        super().__init__(target, *args, **kwargs)
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

    def make_datauri(self, mimetype, data, binary=True):
        parts = ['data:', mimetype]
        if self.charset is not None:
            parts.extend([';charset=', self.charset])
        if self.base64:
            parts.append(';base64')
            from base64 import encodebytes as encode64
            if binary:
                encoded_data = encode64(data).decode(self.charset).replace('\n', '').strip()
            else:
                encoded_data = encode64(data).strip()
        else:
            from urllib.parse import quote_from_bytes, quote
            if binary:
                encoded_data = quote_from_bytes(data)
            else:
                encoded_data = quote(data)
        parts.extend([',', encoded_data])
        return ''.join(parts)


class Buffer2URI(URI2DataURI):
    """Convert buffer to data URI"""

    def convert(self, d):
        if urllib.parse.urlparse(d.uri).scheme == 'data':
            pass
        else:
            d.uri = self.make_datauri(d.mime_type, d.buffer)


class Text2URI(URI2DataURI):
    """Convert text to data URI"""

    def convert(self, d):
        d.uri = self.make_datauri(d.mime_type, d.text, binary=False)


class URI2Text(URI2Buffer):

    def __init__(self, target='text', *args, **kwargs):
        super().__init__(target, *args, **kwargs)

    def convert(self, d):
        if d.mime_type.startswith('text/'):
            super().convert(d)
            d.text = d.buffer.decode()


class All2URI(Text2URI, Buffer2URI):

    def convert(self, d):
        if d.text:
            Text2URI.convert(self, d)
        elif d.buffer:
            Buffer2URI.convert(self, d)
        else:
            raise NotImplementedError
