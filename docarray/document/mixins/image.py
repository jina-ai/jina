import base64
import io
import struct
from typing import Optional, Tuple, Union, BinaryIO

import numpy as np

from .helper import _get_file_context, _uri_to_buffer
from ...helper import T, deprecate_by


class ImageDataMixin:
    """Provide helper functions for :class:`Document` to support image data. """

    def set_image_blob_channel_axis(
        self: T, original_channel_axis: int, new_channel_axis: int
    ) -> T:
        """Move the channel axis of the image :attr:`.blob` inplace.

        :param original_channel_axis: the original axis of the channel
        :param new_channel_axis: the new axis of the channel

        :return: itself after processed
        """
        self.blob = _move_channel_axis(
            self.blob, original_channel_axis, new_channel_axis
        )
        return self

    def convert_buffer_to_image_blob(
        self: T,
        width: Optional[int] = None,
        height: Optional[int] = None,
        channel_axis: int = -1,
    ) -> T:
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

    def convert_image_blob_to_uri(self: T, channel_axis: int = -1) -> T:
        """Assuming :attr:`.blob` is a _valid_ image, set :attr:`uri` accordingly

        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        :return: itself after processed
        """
        blob = _move_channel_axis(self.blob, original_channel_axis=channel_axis)
        png_bytes = _to_png_buffer(blob)
        self.uri = 'data:image/png;base64,' + base64.b64encode(png_bytes).decode()
        return self

    def convert_image_blob_to_buffer(self: T, channel_axis: int = -1) -> T:
        """Assuming :attr:`.blob` is a _valid_ image, set :attr:`buffer` accordingly

        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        :return: itself after processed
        """
        blob = _move_channel_axis(self.blob, original_channel_axis=channel_axis)
        self.buffer = _to_png_buffer(blob)
        return self

    def set_image_blob_shape(
        self: T,
        shape: Tuple[int, int],
        channel_axis: int = -1,
    ) -> T:
        """Resample the image :attr:`.blob` into different size inplace.

        If your current image blob has shape ``[H,W,C]``, then the new blob will be ``[*shape, C]``

        :param shape: the new shape of the image blob.
        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis

        :return: itself after processed
        """
        blob = _move_channel_axis(self.blob, channel_axis, -1)
        out_rows, out_cols = shape
        in_rows, in_cols, n_in = blob.shape

        # compute coordinates to resample
        x = np.tile(np.linspace(0, in_cols - 2, out_cols), out_rows)
        y = np.repeat(np.linspace(0, in_rows - 2, out_rows), out_cols)

        # resample each image
        r = _nn_interpolate_2D(blob, x, y)
        blob = r.reshape(out_rows, out_cols, n_in)
        self.blob = _move_channel_axis(blob, -1, channel_axis)

        return self

    def dump_image_blob_to_file(
        self: T,
        file: Union[str, BinaryIO],
        channel_axis: int = -1,
    ) -> T:
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

    def load_uri_to_image_blob(
        self: T,
        width: Optional[int] = None,
        height: Optional[int] = None,
        channel_axis: int = -1,
    ) -> T:
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

    def set_image_blob_inv_normalization(
        self: T,
        channel_axis: int = -1,
        img_mean: Tuple[float] = (0.485, 0.456, 0.406),
        img_std: Tuple[float] = (0.229, 0.224, 0.225),
    ) -> T:
        """Inverse the normalization of a float32 image :attr:`.blob` into a uint8 image :attr:`.blob` inplace.

        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        :param img_mean: the mean of all images
        :param img_std: the standard deviation of all images
        :return: itself after processed
        """
        if self.blob.dtype == np.float32 and self.blob.ndim == 3:
            blob = _move_channel_axis(self.blob, channel_axis, 0)
            mean = np.asarray(img_mean, dtype=np.float32)
            std = np.asarray(img_std, dtype=np.float32)
            blob = ((blob * std[:, None, None] + mean[:, None, None]) * 255).astype(
                np.uint8
            )
            # set back channel to original
            blob = _move_channel_axis(blob, 0, channel_axis)
            self.blob = blob
        else:
            raise ValueError(
                f'`blob` must be a float32 ndarray with ndim=3, but receiving {self.blob.dtype} with ndim={self.blob.ndim}'
            )
        return self

    def set_image_blob_normalization(
        self: T,
        channel_axis: int = -1,
        img_mean: Tuple[float] = (0.485, 0.456, 0.406),
        img_std: Tuple[float] = (0.229, 0.224, 0.225),
    ) -> T:
        """Normalize a uint8 image :attr:`.blob` into a float32 image :attr:`.blob` inplace.

        Following Pytorch standard, the image must be in the shape of shape (3 x H x W) and
        will be normalized in to a range of [0, 1] and then
        normalized using mean = [0.485, 0.456, 0.406] and std = [0.229, 0.224, 0.225]. These two arrays are computed
        based on millions of images. If you want to train from scratch on your own dataset, you can calculate the new
        mean and std. Otherwise, using the Imagenet pretrianed model with its own mean and std is recommended.

        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        :param img_mean: the mean of all images
        :param img_std: the standard deviation of all images
        :return: itself after processed

        .. warning::
            Please do NOT generalize this function to gray scale, black/white image, it does not make any sense for
            non RGB image. if you look at their MNIST examples, the mean and stddev are 1-dimensional
            (since the inputs are greyscale-- no RGB channels).


        """
        if self.blob.dtype == np.uint8 and self.blob.ndim == 3:
            blob = (self.blob / 255.0).astype(np.float32)
            blob = _move_channel_axis(blob, channel_axis, 0)
            mean = np.asarray(img_mean, dtype=np.float32)
            std = np.asarray(img_std, dtype=np.float32)
            blob = (blob - mean[:, None, None]) / std[:, None, None]
            # set back channel to original
            blob = _move_channel_axis(blob, 0, channel_axis)
            self.blob = blob
        else:
            raise ValueError(
                f'`blob` must be a uint8 ndarray with ndim=3, but receiving {self.blob.dtype} with ndim={self.blob.ndim}'
            )
        return self

    def convert_image_blob_to_sliding_windows(
        self: T,
        window_shape: Tuple[int, int] = (64, 64),
        strides: Optional[Tuple[int, int]] = None,
        padding: bool = False,
        channel_axis: int = -1,
        as_chunks: bool = False,
    ) -> T:
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
        cur_loc_h, cur_loc_w = 0, 0
        if self.location:
            cur_loc_h, cur_loc_w = self.location[:2]

        bbox_locations = [
            (h * stride_h + cur_loc_h, w * stride_w + cur_loc_w, window_h, window_w)
            for h in range(expanded_img.shape[0])
            for w in range(expanded_img.shape[1])
        ]
        expanded_img = expanded_img.reshape((-1, window_h, window_w, c))
        if as_chunks:
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

    convert_uri_to_image_blob = deprecate_by(load_uri_to_image_blob)  #: Deprecated!


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


def _nn_interpolate_2D(X, x, y):
    nx, ny = np.around(x), np.around(y)
    nx = np.clip(nx, 0, X.shape[1] - 1).astype(int)
    ny = np.clip(ny, 0, X.shape[0] - 1).astype(int)
    return X[ny, nx, :]
