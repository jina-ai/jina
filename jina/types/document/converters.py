import base64
import io
import os
import struct
import urllib.parse
import urllib.request
from contextlib import nullcontext
from typing import Optional, overload, Union, BinaryIO

import numpy as np

from ... import __windows__


class ContentConversionMixin:
    """A mixin class for converting, dumping and resizing :attr:`.content` in :class:`Document`."""

    def set_image_blob_channel_axis(
        self, original_channel_axis: int, new_channel_axis: int
    ):
        """Move the channel axis of the image :attr:`.blob` inplace.

        :param original_channel_axis: the original axis of the channel
        :param new_channel_axis: the new axis of the channel
        """
        self.blob = _move_channel_axis(
            self.blob, original_channel_axis, new_channel_axis
        )

    def convert_image_buffer_to_blob(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        channel_axis: int = -1,
    ):
        """Convert an image :attr:`.buffer` to a ndarray :attr:`.blob`.

        :param width: the width of the image blob.
        :param height: the height of the blob.
        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        """
        blob = _to_image_blob(io.BytesIO(self.buffer), width=width, height=height)
        blob = _move_channel_axis(blob, original_channel_axis=channel_axis)
        self.blob = blob

    def convert_image_blob_to_uri(self):
        """Assuming :attr:`.blob` is a _valid_ image, set :attr:`uri` accordingly"""
        png_bytes = _to_png_buffer(self.blob)
        self.uri = 'data:image/png;base64,' + base64.b64encode(png_bytes).decode()

    def resize_image_blob(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        channel_axis: int = -1,
    ):
        """Resize the image :attr:`.blob` inplace.

        :param width: the width of the image blob.
        :param height: the height of the blob.
        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        """
        blob = _move_channel_axis(self.blob, original_channel_axis=channel_axis)
        buffer = _to_png_buffer(blob)
        self.blob = _to_image_blob(io.BytesIO(buffer), width=width, height=height)

    def dump_buffer_to_file(self, file: Union[str, BinaryIO]):
        """Save :attr:`.buffer` into a file

        :param file: File or filename to which the data is saved.
        """
        fp = _get_file_context(file)
        with fp:
            fp.write(self.buffer)

    def dump_image_blob_to_file(self, file: Union[str, BinaryIO]):
        """Save :attr:`.blob` into a file

        :param file: File or filename to which the data is saved.
        """
        fp = _get_file_context(file)
        with fp:
            buffer = _to_png_buffer(self.blob)
            fp.write(buffer)

    def dump_uri_to_file(self, file: Union[str, BinaryIO]):
        """Save :attr:`.uri` into a file

        :param file: File or filename to which the data is saved.
        """
        fp = _get_file_context(file)
        with fp:
            buffer = _uri_to_buffer(self.uri)
            fp.write(buffer)

    def convert_image_uri_to_blob(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        channel_axis: int = -1,
    ):
        """Convert the image-like :attr:`.uri` into :attr:`.blob`

        :param width: the width of the image blob.
        :param height: the height of the blob.
        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        """

        buffer = _uri_to_buffer(self.uri)
        blob = _to_image_blob(io.BytesIO(buffer), width=width, height=height)
        self.blob = _move_channel_axis(blob, original_channel_axis=channel_axis)

    def normalize_image_blob(self, channel_axis: int = -1):
        """Normalize a uint8 image :attr:`.blob` into a float32 image :attr:`.blob` inplace.

        Following Pytorch standard, the image must be in the shape of shape (3 x H x W) and
        will be normalized in to a range of [0, 1] and then
        normalized using mean = [0.485, 0.456, 0.406] and std = [0.229, 0.224, 0.225]. These two arrays are computed
        based on millions of images. If you want to train from scratch on your own dataset, you can calculate the new
        mean and std. Otherwise, using the Imagenet pretrianed model with its own mean and std is recommended.

        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis

        .. warning::
            Please do NOT generalize this function to gray scale, black/white image, it does not make any sense for
            non RGB image. if you look at their MNIST examples, the mean and stddev are 1-dimensional
            (since the inputs are greyscale-- no RGB channels).
        """
        if self.blob.dtype == np.uint8 and self.blob.ndim == 3:
            blob = (self.blob / 255.0).astype(np.float32)
            blob = _move_channel_axis(blob, channel_axis, 0)
            mean = np.asarray([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.asarray([0.229, 0.224, 0.225], dtype=np.float32)
            blob = (blob - mean[:, None, None]) / std[:, None, None]
            # set back channel to original
            blob = _move_channel_axis(blob, 0, channel_axis)
            self.blob = blob
        else:
            raise ValueError(
                f'`blob` must be a uint8 ndarray with ndim=3, but receiving {self.blob.dtype} with ndim={self.blob.ndim}'
            )

    @overload
    def convert_buffer_to_blob(
        self, dtype: Optional[str] = None, count: int = -1, offset: int = 0
    ):
        """Assuming the :attr:`buffer` is a _valid_ buffer of Numpy ndarray,
        set :attr:`blob` accordingly.

        :param dtype: Data-type of the returned array; default: float.
        :param count: Number of items to read. ``-1`` means all data in the buffer.
        :param offset: Start reading the buffer from this offset (in bytes); default: 0.

        .. note::
            One can only recover values not shape information from pure buffer.
        """
        ...

    def convert_buffer_to_blob(self, *args, **kwargs):
        """Convert :attr:`.buffer` to :attr:`.blob` inplace.

        # noqa: DAR101
        """
        self.blob = np.frombuffer(self.buffer, *args, **kwargs)

    def convert_blob_to_buffer(self):
        """Convert :attr:`.blob` to :attr:`.buffer` inplace. """
        self.buffer = self.blob.tobytes()

    def convert_uri_to_buffer(self):
        """Convert :attr:`.uri` to :attr:`.buffer` inplace.
        Internally it downloads from the URI and set :attr:`buffer`.

        """
        self.buffer = _uri_to_buffer(self.uri)

    def convert_uri_to_datauri(self, charset: str = 'utf-8', base64: bool = False):
        """Convert :attr:`.uri` to dataURI and store it in :attr:`.uri` inplace.

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit. Designed to be efficient for non-text 8 bit and binary data. Sometimes used for text data that frequently uses non-US-ASCII characters.
        """
        if not _is_datauri(self.uri):
            buffer = _uri_to_buffer(self.uri)
            self.uri = _to_datauri(self.mime_type, buffer, charset, base64, binary=True)

    def convert_buffer_to_uri(self, charset: str = 'utf-8', base64: bool = False):
        """Convert :attr:`.buffer` to data :attr:`.uri` in place.
        Internally it first reads into buffer and then converts it to data URI.

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit.
            Designed to be efficient for non-text 8 bit and binary data. Sometimes used for text data that
            frequently uses non-US-ASCII characters.
        """

        if not self.mime_type:
            raise ValueError(
                f'{self.mime_type} is unset, can not convert it to data uri'
            )

        self.uri = _to_datauri(
            self.mime_type, self.buffer, charset, base64, binary=True
        )

    def convert_text_to_uri(self, charset: str = 'utf-8', base64: bool = False):
        """Convert :attr:`.text` to data :attr:`.uri`.

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit.
            Designed to be efficient for non-text 8 bit and binary data.
            Sometimes used for text data that frequently uses non-US-ASCII characters.
        """

        self.uri = _to_datauri(self.mime_type, self.text, charset, base64, binary=False)

    def convert_uri_to_text(self):
        """Convert :attr:`.uri` to :attr`.text` inplace."""
        buffer = _uri_to_buffer(self.uri)
        self.text = buffer.decode()

    def convert_content_to_uri(self):
        """Convert :attr:`.content` in :attr:`.uri` inplace with best effort"""
        if self.text:
            self.convert_text_to_uri()
        elif self.buffer:
            self.convert_buffer_to_uri()
        elif self.content_type:
            raise NotImplementedError


def _uri_to_buffer(uri: str) -> bytes:
    """Convert uri to buffer
    Internally it reads uri into buffer.

    :param uri: the uri of Document
    :return: buffer bytes.
    """
    if urllib.parse.urlparse(uri).scheme in {'http', 'https', 'data'}:
        req = urllib.request.Request(uri, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as fp:
            return fp.read()
    elif os.path.exists(uri):
        with open(uri, 'rb') as fp:
            return fp.read()
    else:
        raise FileNotFoundError(f'{uri} is not a URL or a valid local path')


def _png_to_buffer_1d(arr: 'np.ndarray', width: int, height: int) -> bytes:
    import zlib

    pixels = []
    for p in arr[::-1]:
        pixels.extend([p, p, p, 255])
    buf = bytearray(pixels)

    # reverse the vertical line order and add null bytes at the start
    width_byte_4 = width * 4
    raw_data = b''.join(
        b'\x00' + buf[span : span + width_byte_4]
        for span in range((height - 1) * width_byte_4, -1, -width_byte_4)
    )

    def png_pack(png_tag, data):
        chunk_head = png_tag + data
        return (
            struct.pack('!I', len(data))
            + chunk_head
            + struct.pack('!I', 0xFFFFFFFF & zlib.crc32(chunk_head))
        )

    png_bytes = b''.join(
        [
            b'\x89PNG\r\n\x1a\n',
            png_pack(b'IHDR', struct.pack('!2I5B', width, height, 8, 6, 0, 0, 0)),
            png_pack(b'IDAT', zlib.compress(raw_data, 9)),
            png_pack(b'IEND', b''),
        ]
    )

    return png_bytes


def _pillow_image_to_buffer(image, image_format: str) -> bytes:
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format=image_format)
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr


def _to_png_buffer(arr: 'np.ndarray') -> bytes:
    """
    Convert png to buffer bytes.

    :param arr: Data representations of the png.
    :return: Png in buffer bytes.

    ..note::
        if both :attr:`width` and :attr:`height` were provided, will not resize. Otherwise, will get image size
        by :attr:`arr` shape and apply resize method :attr:`resize_method`.
    """
    arr = arr.astype(np.uint8).squeeze()

    if arr.ndim == 1:
        # note this should be only used for MNIST/FashionMNIST dataset, because of the nature of these two datasets
        # no other image data should flattened into 1-dim array.
        png_bytes = _png_to_buffer_1d(arr, 28, 28)
    elif arr.ndim == 2:
        from PIL import Image

        im = Image.fromarray(arr).convert('L')
        png_bytes = _pillow_image_to_buffer(im, image_format='PNG')
    elif arr.ndim == 3:
        from PIL import Image

        im = Image.fromarray(arr).convert('RGB')
        png_bytes = _pillow_image_to_buffer(im, image_format='PNG')
    else:
        raise ValueError(
            f'{arr.shape} ndarray can not be converted into an image buffer.'
        )

    return png_bytes


def _move_channel_axis(
    blob: np.ndarray, original_channel_axis: int = -1, target_channel_axis: int = -1
) -> np.ndarray:
    """This will always make the channel axis to the last of the :attr:`.blob`

    #noqa: DAR101
    #noqa: DAR201
    """
    if original_channel_axis != target_channel_axis:
        blob = np.moveaxis(blob, original_channel_axis, target_channel_axis)
    return blob


def _to_image_blob(
    source,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> 'np.ndarray':
    """
    Convert an image buffer to blob

    :param source: binary buffer or file path
    :param width: the width of the image blob.
    :param height: the height of the blob.
    :return: image blob
    """
    from PIL import Image

    raw_img = Image.open(source)
    if width or height:
        new_width = width or raw_img.width
        new_height = height or raw_img.height
        raw_img = raw_img.resize((new_width, new_height))
    return np.array(raw_img)


def _to_datauri(
    mimetype, data, charset: str = 'utf-8', base64: bool = False, binary: bool = True
) -> str:
    """
    Convert data to data URI.

    :param mimetype: MIME types (e.g. 'text/plain','image/png' etc.)
    :param data: Data representations.
    :param charset: Charset may be any character set registered with IANA
    :param base64: Used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit. Designed to be efficient for non-text 8 bit and binary data. Sometimes used for text data that frequently uses non-US-ASCII characters.
    :param binary: True if from binary data False for other data (e.g. text)
    :return: URI data
    """
    parts = ['data:', mimetype]
    if charset is not None:
        parts.extend([';charset=', charset])
    if base64:
        parts.append(';base64')
        from base64 import encodebytes as encode64

        if binary:
            encoded_data = encode64(data).decode(charset).replace('\n', '').strip()
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


def _is_uri(value: str) -> bool:
    scheme = urllib.parse.urlparse(value).scheme
    return (
        (scheme in {'http', 'https'})
        or (scheme in {'data'})
        or os.path.exists(value)
        or os.access(os.path.dirname(value), os.W_OK)
    )


def _is_datauri(value: str) -> bool:
    scheme = urllib.parse.urlparse(value).scheme
    return scheme in {'data'}


def _get_file_context(file):
    if hasattr(file, 'write'):
        file_ctx = nullcontext(file)
    else:
        if __windows__:
            file_ctx = open(file, 'wb', newline='')
        else:
            file_ctx = open(file, 'wb')

    return file_ctx
