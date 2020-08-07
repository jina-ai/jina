__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple, Union

import numpy as np


def _move_channel_axis(img: 'np.ndarray', channel_axis_to_move: int, target_channel_axis: int = -1) -> 'np.ndarray':
    """
    Ensure the color channel axis is the default axis.
    """
    if channel_axis_to_move == target_channel_axis:
        return img
    return np.moveaxis(img, channel_axis_to_move, target_channel_axis)


def _load_image(blob: 'np.ndarray', channel_axis: int):
    """
    Load an image array and return a `PIL.Image` object.
    """

    from PIL import Image
    img = _move_channel_axis(blob, channel_axis)
    return Image.fromarray(img.astype('uint8'))


def _crop_image(img, target_size: Union[Tuple[int, int], int], top: int = None, left: int = None, how: str = 'precise'):
    """
    Crop the input :py:mod:`PIL` image.

    :param img: :py:mod:`PIL.Image`, the image to be resized
    :param target_size: desired output size. If size is a sequence like
        (h, w), the output size will be matched to this. If size is an int,
        the output will have the same height and width as the `target_size`.
    :param top: the vertical coordinate of the top left corner of the crop box.
    :param left: the horizontal coordinate of the top left corner of the crop box.
    :param how: the way of cropping. Valid values include `center`, `random`, and, `precise`. Default is `precise`.
        - `center`: crop the center part of the image
        - `random`: crop a random part of the image
        - `precise`: crop the part of the image specified by the crop box with the given ``top`` and ``left``.
        .. warning:: When `precise` is used, ``top`` and ``left`` must be fed valid value.

    """
    import PIL.Image as Image
    assert isinstance(img, Image.Image), 'img must be a PIL.Image'
    img_w, img_h = img.size
    if isinstance(target_size, int):
        target_h = target_w = target_size
    elif isinstance(target_size, Tuple) and len(target_size) == 2:
        target_h, target_w = target_size
    else:
        raise ValueError(f'target_size should be an integer or a tuple of two integers: {target_size}')
    w_beg = left
    h_beg = top
    if how == 'center':
        w_beg = int((img_w - target_w) / 2)
        h_beg = int((img_h - target_h) / 2)
    elif how == 'random':
        w_beg = np.random.randint(0, img_w - target_w + 1)
        h_beg = np.random.randint(0, img_h - target_h + 1)
    elif how == 'precise':
        assert (w_beg is not None and h_beg is not None)
        assert (0 <= w_beg <= (img_w - target_w)), f'left must be within [0, {img_w - target_w}]: {w_beg}'
        assert (0 <= h_beg <= (img_h - target_h)), f'top must be within [0, {img_h - target_h}]: {h_beg}'
    else:
        raise ValueError(f'unknown input how: {how}')
    if not isinstance(w_beg, int):
        raise ValueError(f'left must be int number between 0 and {img_w}: {left}')
    if not isinstance(h_beg, int):
        raise ValueError(f'top must be int number between 0 and {img_h}: {top}')
    w_end = w_beg + target_w
    h_end = h_beg + target_h
    img = img.crop((w_beg, h_beg, w_end, h_end))
    return img, h_beg, w_beg


def _resize_short(img, target_size: Union[Tuple[int, int], int], how: str = 'LANCZOS'):
    """
    Resize the input :py:mod:`PIL` image.
    :param img: :py:mod:`PIL.Image`, the image to be resized
    :param target_size: desired output size. If size is a sequence like (h, w), the output size will be matched to
        this. If size is an int, the smaller edge of the image will be matched to this number maintain the aspect
        ratio.
    :param how: the interpolation method. Valid values include `NEAREST`, `BILINEAR`, `BICUBIC`, and `LANCZOS`.
        Default is `LANCZOS`. Please refer to `PIL.Image` for detaisl.
    """
    import PIL.Image as Image
    assert isinstance(img, Image.Image), 'img must be a PIL.Image'
    if isinstance(target_size, int):
        percent = float(target_size) / min(img.size[0], img.size[1])
        target_w = int(round(img.size[0] * percent))
        target_h = int(round(img.size[1] * percent))
    elif isinstance(target_size, Tuple) and len(target_size) == 2:
        target_h, target_w = target_size
    else:
        raise ValueError(f'target_size should be an integer or a tuple of two integers: {target_size}')
    img = img.resize((target_w, target_h), getattr(Image, how))
    return img
