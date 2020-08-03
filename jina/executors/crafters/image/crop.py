__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple, Dict, Union

import numpy as np

from .. import BaseCrafter
from .helper import _crop_image, _restore_channel_axis, _load_image


class ImageCropper(BaseCrafter):
    """
    :class:`ImageCropper` crops the image with the specific crop box. The coordinate is the same coordinate-system in
        the :py:mode:`PIL.Image`.
    """

    def __init__(self, top: int, left: int, height: int, width: int, channel_axis: int = -1, *args, **kwargs):
        """

        :param top: the vertical coordinate of the top left corner of the crop box.
        :param left: the horizontal coordinate of the top left corner of the crop box.
        :param height: the height of the crop box.
        :param width: the width of the crop box.
        :param channel_axis: the axis refering to the channels
        """
        super().__init__(*args, **kwargs)
        self.top = top
        self.left = left
        self.height = height
        self.width = width
        self.channel_axis = channel_axis

    def craft(self, blob: 'np.ndarray', *args, **kwargs) -> Dict:
        """
        Crop the input image array.

        :param blob: the ndarray of the image
        :returns: a chunk dict with the cropped image
        """
        raw_img = _load_image(blob, self.channel_axis)
        _img = _crop_image(raw_img, (self.width, self.height), self.left, self.top)
        img = _restore_channel_axis(np.asarray(_img), self.channel_axis)
        return dict(offset=0, weight=1., blob=img.astype('float32'))


class CenterImageCropper(BaseCrafter):
    """
    :class:`CenterImageCropper` crops the image with the center crop box. The coordinate is the same coordinate-system
        in the :py:mode:`PIL.Image`.
    """

    def __init__(self,
                 target_size: Union[Tuple[int], int],
                 channel_axis: int = -1,
                 *args,
                 **kwargs):
        """

        :param target_size: desired output size. If size is a sequence like (h, w), the output size will be matched to
            this. If size is an int, the output will have the same height and width as the `target_size`.
        """
        super().__init__(*args, **kwargs)
        self.target_size = target_size
        self.channel_axis = channel_axis

    def craft(self, blob: 'np.ndarray', *args, **kwargs) -> Dict:
        """
        Crop the input image array.

        :param blob: the ndarray of the image
        :return: a chunk dict with the cropped image
        """
        raw_img = _load_image(blob, self.channel_axis)
        _img = _crop_image(raw_img, self.target_size, how='center')
        img = _restore_channel_axis(np.asarray(_img), self.channel_axis)
        return dict(offset=0, weight=1., blob=img.astype('float32'))
