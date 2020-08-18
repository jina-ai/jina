__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


from typing import Union, Tuple, Dict

import numpy as np
from jina.executors.crafters import BaseCrafter

from .helper import _load_image, _move_channel_axis, _resize_short


class ImageResizer(BaseCrafter):
    """
    :class:`ImageResizer` resize the image to the given size.
    """

    def __init__(self,
                 target_size: Union[Tuple[int, int], int],
                 how: str = 'BILINEAR',
                 channel_axis: int = -1,
                 *args, **kwargs):
        """

        :param target_size: desired output size. If size is a sequence like (h, w), the output size will be matched to
            this. If size is an int, the smaller edge of the image will be matched to this number maintain the aspect
            ratio.
        :param how: the interpolation method. Valid values include `NEAREST`, `BILINEAR`, `BICUBIC`, and `LANCZOS`.
            Default is `BILINEAR`. Please refer to `PIL.Image` for detaisl.
        """
        super().__init__(*args, **kwargs)
        if isinstance(target_size, int):
            self.output_dim = target_size
        else:
            raise ValueError(f'output_dim {target_size} should be an integer')
        self.how = how
        self.channel_axis = channel_axis

    def craft(self, blob: 'np.ndarray', *args, **kwargs) -> Dict:
        """
        Resize the image array to the given size.

        :param blob: the ndarray of the image
        :return: a chunk dict with the cropped image
        """
        raw_img = _load_image(blob, self.channel_axis)
        _img = _resize_short(raw_img, self.output_dim, self.how)
        img = _move_channel_axis(np.asarray(_img), -1, self.channel_axis)
        return dict(offset=0, weight=1., blob=img.astype('float32'))
