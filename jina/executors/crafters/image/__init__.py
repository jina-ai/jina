__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple, Union

import numpy as np

from .. import BaseChunkCrafter


class ImageChunkCrafter(BaseChunkCrafter):
    """
    :class:`ImageChunkCrafter` provides the basic functions for processing image data on chunk-level.

    .. warning::
        :class:'ImageChunkCrafter' is intended to be used internally.

    """

    def __init__(self, channel_axis: int = -1, *args, **kwargs):
        """

        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        """
        super().__init__(*args, **kwargs)
        self.channel_axis = channel_axis

    def check_channel_axis(self, img: 'np.ndarray') -> 'np.ndarray':
        """
        Ensure the color channel axis is the last axis.
        """
        if self.channel_axis == -1:
            return img
        return np.moveaxis(img, self.channel_axis, -1)

    def restore_channel_axis(self, img: 'np.ndarray') -> 'np.ndarray':
        if self.channel_axis == -1:
            return img
        return np.moveaxis(img, -1, self.channel_axis)

    def load_image(self, blob: 'np.ndarray'):
        """
        Load an image array and return a `PIL.Image` object.
        """

        from PIL import Image
        img = self.check_channel_axis(blob)
        return Image.fromarray(img.astype('uint8'))

    @staticmethod
    def _resize_short(img, target_size: Union[Tuple[int], int], how: str = 'LANCZOS'):
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
            raise ValueError('target_size should be an integer or a tuple of two integers: {}'.format(target_size))
        img = img.resize((target_w, target_h), getattr(Image, how))
        return img

    @staticmethod
    def _crop_image(img, target_size: Union[Tuple[int], int], top: int = None, left: int = None, how: str = 'precise'):
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
            raise ValueError('target_size should be an integer or a tuple of two integers: {}'.format(target_size))
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
            assert (0 <= w_beg <= (img_w - target_w)), 'left must be within [0, {}]: {}'.format(img_w - target_w, w_beg)
            assert (0 <= h_beg <= (img_h - target_h)), 'top must be within [0, {}]: {}'.format(img_h - target_h, h_beg)
        else:
            raise ValueError('unknown input how: {}'.format(how))
        if not isinstance(w_beg, int):
            raise ValueError('left must be int number between 0 and {}: {}'.format(img_w, left))
        if not isinstance(h_beg, int):
            raise ValueError('top must be int number between 0 and {}: {}'.format(img_h, top))
        w_end = w_beg + target_w
        h_end = h_beg + target_h
        img = img.crop((w_beg, h_beg, w_end, h_end))
        return img
