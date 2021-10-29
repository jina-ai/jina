import base64
import io
import os
import struct
import urllib.parse
import urllib.request
import wave
from contextlib import nullcontext
from typing import Optional, Union, BinaryIO, TYPE_CHECKING, Dict, Tuple

import numpy as np

from ... import __windows__

if TYPE_CHECKING:
    from . import Document


class ContentConversionMixin:
    """A mixin class for converting, dumping and resizing :attr:`.content` in :class:`Document`.

    Note that most of the functions, except the ``dump_*`` ones can be used in a chain, e.g.

    .. highlight:: python
    .. code-block:: python

        for d in from_files('/Users/hanxiao/Documents/tmpimg/*.jpg'):
            yield (
                d.convert_image_uri_to_blob()
                .convert_uri_to_datauri()
                .resize_image_blob(224, 224)
                .normalize_image_blob()
                .set_image_blob_channel_axis(-1, 0)
            )
    """

    def set_image_blob_channel_axis(
        self, original_channel_axis: int, new_channel_axis: int
    ) -> 'Document':
        """Move the channel axis of the image :attr:`.blob` inplace.

        :param original_channel_axis: the original axis of the channel
        :param new_channel_axis: the new axis of the channel

        :return: itself after processed
        """
        self.blob = _move_channel_axis(
            self.blob, original_channel_axis, new_channel_axis
        )
        return self

    def convert_image_buffer_to_blob(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        channel_axis: int = -1,
    ) -> 'Document':
        """Convert an image :attr:`.buffer` to a ndarray :attr:`.blob`.

        :param width: the width of the image blob.
        :param height: the height of the blob.
        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis

        :return: itself after processed
        """
        blob = _to_image_blob(io.BytesIO(self.buffer), width=width, height=height)
        blob = _move_channel_axis(blob, original_channel_axis=channel_axis)
        self.blob = blob
        return self

    def convert_image_blob_to_uri(self) -> 'Document':
        """Assuming :attr:`.blob` is a _valid_ image, set :attr:`uri` accordingly

        :return: itself after processed
        """
        png_bytes = _to_png_buffer(self.blob)
        self.uri = 'data:image/png;base64,' + base64.b64encode(png_bytes).decode()
        return self

    def resize_image_blob(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        channel_axis: int = -1,
    ) -> 'Document':
        """Resize the image :attr:`.blob` inplace.

        :param width: the width of the image blob.
        :param height: the height of the blob.
        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis

        :return: itself after processed
        """
        blob = _move_channel_axis(self.blob, original_channel_axis=channel_axis)
        buffer = _to_png_buffer(blob)
        self.blob = _to_image_blob(io.BytesIO(buffer), width=width, height=height)
        return self

    def dump_buffer_to_file(self, file: Union[str, BinaryIO]) -> 'Document':
        """Save :attr:`.buffer` into a file

        :param file: File or filename to which the data is saved.
        :return: itself after processed
        """
        fp = _get_file_context(file)
        with fp:
            fp.write(self.buffer)
        return self

    def dump_image_blob_to_file(
        self,
        file: Union[str, BinaryIO],
        channel_axis: int = -1,
    ) -> 'Document':
        """Save :attr:`.blob` into a file

        :param file: File or filename to which the data is saved.
        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis

        :return: itself after processed
        """
        fp = _get_file_context(file)
        with fp:
            blob = _move_channel_axis(self.blob, channel_axis, -1)
            buffer = _to_png_buffer(blob)
            fp.write(buffer)
        return self

    def dump_uri_to_file(self, file: Union[str, BinaryIO]) -> 'Document':
        """Save :attr:`.uri` into a file

        :param file: File or filename to which the data is saved.

        :return: itself after processed
        """
        fp = _get_file_context(file)
        with fp:
            buffer = _uri_to_buffer(self.uri)
            fp.write(buffer)
        return self

    def dump_audio_blob_to_file(
        self,
        file: Union[str, BinaryIO],
        sample_rate: int = 44100,
        sample_width: int = 2,
    ) -> 'Document':
        """Save :attr:`.blob` into an wav file. Mono/stereo is preserved.

        :param file: if file is a string, open the file by that name, otherwise treat it as a file-like object.
        :param sample_rate: sampling frequency
        :param sample_width: sample width in bytes

        :return: Document itself after processed
        """
        # Convert to (little-endian) 16 bit integers.
        max_int16 = 2 ** 15
        blob = (self.blob * max_int16).astype('<h')
        n_channels = 2 if self.blob.ndim > 1 else 1

        with wave.open(file, 'w') as f:
            # 2 Channels.
            f.setnchannels(n_channels)
            # 2 bytes per sample.
            f.setsampwidth(sample_width)
            f.setframerate(sample_rate)
            f.writeframes(blob.tobytes())
        return self

    def convert_audio_uri_to_blob(self) -> 'Document':
        """Convert an audio :attr:`.uri` into :attr:`.blob` inplace

        :return: Document itself after processed
        """
        ifile = wave.open(
            self.uri
        )  #: note wave is Python built-in module https://docs.python.org/3/library/wave.html
        samples = ifile.getnframes()
        audio = ifile.readframes(samples)

        # Convert buffer to float32 using NumPy
        audio_as_np_int16 = np.frombuffer(audio, dtype=np.int16)
        audio_as_np_float32 = audio_as_np_int16.astype(np.float32)

        # Normalise float32 array so that values are between -1.0 and +1.0
        max_int16 = 2 ** 15
        audio_normalised = audio_as_np_float32 / max_int16

        channels = ifile.getnchannels()
        if channels == 2:
            # 1 for mono, 2 for stereo
            audio_stereo = np.empty((int(len(audio_normalised) / channels), channels))
            audio_stereo[:, 0] = audio_normalised[range(0, len(audio_normalised), 2)]
            audio_stereo[:, 1] = audio_normalised[range(1, len(audio_normalised), 2)]

            self.blob = audio_stereo
        else:
            self.blob = audio_normalised
        return self

    def convert_image_uri_to_blob(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        channel_axis: int = -1,
    ) -> 'Document':
        """Convert the image-like :attr:`.uri` into :attr:`.blob`

        :param width: the width of the image blob.
        :param height: the height of the blob.
        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis

        :return: itself after processed
        """

        buffer = _uri_to_buffer(self.uri)
        blob = _to_image_blob(io.BytesIO(buffer), width=width, height=height)
        self.blob = _move_channel_axis(blob, original_channel_axis=channel_axis)
        return self

    def normalize_image_blob(self, channel_axis: int = -1) -> 'Document':
        """Normalize a uint8 image :attr:`.blob` into a float32 image :attr:`.blob` inplace.

        Following Pytorch standard, the image must be in the shape of shape (3 x H x W) and
        will be normalized in to a range of [0, 1] and then
        normalized using mean = [0.485, 0.456, 0.406] and std = [0.229, 0.224, 0.225]. These two arrays are computed
        based on millions of images. If you want to train from scratch on your own dataset, you can calculate the new
        mean and std. Otherwise, using the Imagenet pretrianed model with its own mean and std is recommended.

        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        :return: itself after processed

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
        return self

    def convert_buffer_to_blob(
        self, dtype: Optional[str] = None, count: int = -1, offset: int = 0
    ) -> 'Document':
        """Assuming the :attr:`buffer` is a _valid_ buffer of Numpy ndarray,
        set :attr:`blob` accordingly.

        :param dtype: Data-type of the returned array; default: float.
        :param count: Number of items to read. ``-1`` means all data in the buffer.
        :param offset: Start reading the buffer from this offset (in bytes); default: 0.

        :return: itself after processed
        """
        self.blob = np.frombuffer(self.buffer, dtype=dtype, count=count, offset=offset)
        return self

    def convert_blob_to_buffer(self) -> 'Document':
        """Convert :attr:`.blob` to :attr:`.buffer` inplace.

        :return: itself after processed
        """
        self.buffer = self.blob.tobytes()
        return self

    def convert_uri_to_buffer(self) -> 'Document':
        """Convert :attr:`.uri` to :attr:`.buffer` inplace.
        Internally it downloads from the URI and set :attr:`buffer`.

        :return: itself after processed
        """
        self.buffer = _uri_to_buffer(self.uri)
        return self

    def convert_uri_to_datauri(
        self, charset: str = 'utf-8', base64: bool = False
    ) -> 'Document':
        """Convert :attr:`.uri` to dataURI and store it in :attr:`.uri` inplace.

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit. Designed to be efficient for non-text 8 bit and binary data. Sometimes used for text data that frequently uses non-US-ASCII characters.

        :return: itself after processed
        """
        if not _is_datauri(self.uri):
            buffer = _uri_to_buffer(self.uri)
            self.uri = _to_datauri(self.mime_type, buffer, charset, base64, binary=True)
        return self

    def convert_buffer_to_uri(
        self, charset: str = 'utf-8', base64: bool = False
    ) -> 'Document':
        """Convert :attr:`.buffer` to data :attr:`.uri` in place.
        Internally it first reads into buffer and then converts it to data URI.

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit.
            Designed to be efficient for non-text 8 bit and binary data. Sometimes used for text data that
            frequently uses non-US-ASCII characters.

        :return: itself after processed
        """

        if not self.mime_type:
            raise ValueError(
                f'{self.mime_type} is unset, can not convert it to data uri'
            )

        self.uri = _to_datauri(
            self.mime_type, self.buffer, charset, base64, binary=True
        )
        return self

    def convert_text_to_uri(
        self, charset: str = 'utf-8', base64: bool = False
    ) -> 'Document':
        """Convert :attr:`.text` to data :attr:`.uri`.

        :param charset: charset may be any character set registered with IANA
        :param base64: used to encode arbitrary octet sequences into a form that satisfies the rules of 7bit.
            Designed to be efficient for non-text 8 bit and binary data.
            Sometimes used for text data that frequently uses non-US-ASCII characters.

        :return: itself after processed
        """

        self.uri = _to_datauri(self.mime_type, self.text, charset, base64, binary=False)
        return self

    def convert_uri_to_text(self) -> 'Document':
        """Convert :attr:`.uri` to :attr`.text` inplace.

        :return: itself after processed
        """
        buffer = _uri_to_buffer(self.uri)
        self.text = buffer.decode()
        return self

    def convert_content_to_uri(self) -> 'Document':
        """Convert :attr:`.content` in :attr:`.uri` inplace with best effort

        :return: itself after processed
        """
        if self.text:
            self.convert_text_to_uri()
        elif self.buffer:
            self.convert_buffer_to_uri()
        elif self.content_type:
            raise NotImplementedError
        return self

    def convert_text_to_blob(
        self,
        vocab: Dict[str, int],
        max_length: Optional[int] = None,
        dtype: str = 'int64',
    ) -> 'Document':
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
        self, vocab: Union[Dict[str, int], Dict[int, str]], delimiter: str = ' '
    ) -> 'Document':
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

    def convert_image_blob_to_sliding_windows(
        self,
        window_shape: Tuple[int, int] = (64, 64),
        strides: Optional[Tuple[int, int]] = None,
        padding: bool = False,
        channel_axis: int = -1,
        as_chunks: bool = False,
    ) -> 'Document':
        """Convert :attr:`.blob` into a sliding window view with the given window shape :attr:`.blob` inplace.

        :param window_shape: desired output size. If size is a sequence like (h, w), the output size will be matched to
            this. If size is an int, the output will have the same height and width as the `target_size`.
        :param strides: the strides between two neighboring sliding windows. `strides` is a sequence like (h, w), in
            which denote the strides on the vertical and the horizontal axis. When not given, using `window_shape`
        :param padding: If False, only patches which are fully contained in the input image are included. If True,
            all patches whose starting point is inside the input are included, and areas outside the input default to
            zero. The `padding` argument has no effect on the size of each patch, it determines how many patches are
            extracted. Default is False.
        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis.
        :param as_chunks: If set, each sliding window will be stored in the chunk of the current Document
        :return: Document itself after processed
        """
        window_h, window_w = window_shape
        stride_h, stride_w = strides or window_shape
        blob = _move_channel_axis(self.blob, channel_axis, -1)
        if padding:
            h, w, c = blob.shape
            ext_h = window_h - h % stride_h
            ext_w = window_w - w % window_w
            blob = np.pad(
                blob,
                ((0, ext_h), (0, ext_w), (0, 0)),
                mode='constant',
                constant_values=0,
            )
        h, w, c = blob.shape
        row_step = blob.strides[0]
        col_step = blob.strides[1]

        expanded_img = np.lib.stride_tricks.as_strided(
            blob,
            shape=(
                1 + int((h - window_h) / stride_h),
                1 + int((w - window_w) / stride_w),
                window_h,
                window_w,
                c,
            ),
            strides=(row_step * stride_h, col_step * stride_w, row_step, col_step, 1),
            writeable=False,
        )

        expanded_img = expanded_img.reshape((-1, window_h, window_w, c))
        if as_chunks:
            bbox_locations = [
                (h * stride_h, w * stride_w)
                for h in range(expanded_img.shape[0])
                for w in range(expanded_img.shape[1])
            ]
            from . import Document

            for location, _blob in zip(bbox_locations, expanded_img):
                self.chunks.append(
                    Document(
                        blob=_move_channel_axis(_blob, -1, channel_axis),
                        location=location,
                    )
                )
        else:
            self.blob = _move_channel_axis(expanded_img, -1, channel_axis)
        return self


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
    try:
        return np.array(raw_img.convert('RGB'))
    except:
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
