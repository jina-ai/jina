from typing import Dict

import numpy as np

from .. import BaseCrafter
from .helper import _restore_channel_axis, _load_image


class ImageFlipper(BaseCrafter):
    """
    :class:`ImageFlipper` flips the image horizontally or vertically. Flip image in the left/right or up/down direction respectively.
    """

    def __init__(self,
                 vertical: bool = False,
                 channel_axis: int = -1,
                 *args,
                 **kwargs):
        """

        :param vertical: desired rotation type. ``True`` indicates the image should be flipped vertically.
        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        """
        super().__init__(*args, **kwargs)
        self.vertical = vertical
        self.channel_axis = channel_axis

    def craft(self, blob: 'np.ndarray', *args, **kwargs) -> Dict:
        """
        Flip the input image array.

        :param blob: the ndarray of the image with the color channel at the last axis
        :return: a chunk dict with the mage
        """
        raw_img = _load_image(blob, self.channel_axis)
        _img = self._flip_image(raw_img)
        img = _restore_channel_axis(_img, self.channel_axis)
        return dict(offset=0, weight=1., blob=img)

    def _flip_image(self, img):
        img = np.array(img).astype('float32')
        if self.vertical:
            return np.flipud(img)
        else:
            return np.fliplr(img)
