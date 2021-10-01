import struct
import zlib
from typing import Optional

import numpy as np


def _png_to_buffer_1d(arr: 'np.ndarray', width: int, height: int) -> bytes:
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
    import io

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format=image_format)
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr


def png_to_buffer(
    arr: 'np.ndarray',
    width: Optional[int] = None,
    height: Optional[int] = None,
    resize_method: str = 'BILINEAR',
    color_axis: int = -1,
):
    """
    Convert png to buffer bytes.

    :param arr: Data representations of the png.
    :param width: the width of the :attr:`arr`, if None, interpret from :attr:`arr` shape.
    :param height: the height of the :attr:`arr`, if None, interpret from :attr:`arr` shape.
    :param resize_method: Resize methods (e.g. `NEAREST`, `BILINEAR`, `BICUBIC`, and `LANCZOS`).
    :param color_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
    :return: Png in buffer bytes.

    ..note::
        if both :attr:`width` and :attr:`height` were provided, will not resize. Otherwise, will get image size
        by :attr:`arr` shape and apply resize method :attr:`resize_method`.
    """
    arr = arr.astype(np.uint8)
    is_height_width_set = bool(height and width)

    if arr.ndim == 1:
        if not is_height_width_set:
            height, width = arr.shape[0], 1
        png_bytes = _png_to_buffer_1d(arr, width, height)
    elif arr.ndim == 2:
        from PIL import Image

        if not is_height_width_set:
            height, width = arr.shape
            im = Image.fromarray(arr).convert('L')
            im = im.resize((width, height), getattr(Image, resize_method))
        else:
            im = Image.fromarray(arr).convert('L')
        png_bytes = _pillow_image_to_buffer(im, image_format='PNG')
    elif arr.ndim == 3:
        from PIL import Image

        if color_axis != -1:
            arr = np.moveaxis(arr, color_axis, -1)

        if not is_height_width_set:
            height, width, num_channels = arr.shape
        else:
            _, _, num_channels = arr.shape

        if num_channels == 1:  # greyscale image
            im = Image.fromarray((arr[0] * 255).astype(np.uint8))
        else:
            im = Image.fromarray(arr).convert('RGB')

        if not is_height_width_set:
            im = im.resize((width, height), getattr(Image, resize_method))

        png_bytes = _pillow_image_to_buffer(im, image_format='PNG')
    else:
        raise ValueError(f'ndim={len(arr.shape)} array is not supported')

    return png_bytes


def to_image_blob(source, color_axis: int = -1) -> 'np.ndarray':
    """
    Convert an image buffer to blob

    :param source: image bytes buffer
    :param color_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
    :return: image blob
    """
    from PIL import Image

    raw_img = Image.open(source).convert('RGB')
    img = np.array(raw_img).astype('float32')
    if color_axis != -1:
        img = np.moveaxis(img, -1, color_axis)
    return img


def to_datauri(
    mimetype, data, charset: str = 'utf-8', base64: bool = False, binary: bool = True
):
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
