__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import numbers
from typing import Union, Tuple, Dict

import numpy as np

from . import ImageChunkCrafter


class ImageResizer(ImageChunkCrafter):
    """
    :class:`ImageResizer` resize the image to the given size.
    """

    def __init__(self,
                 target_size: Union[Tuple[int], int],
                 how='BILINEAR',
                 *args, **kwargs):
        """

        :param target_size: desired output size. If size is a sequence like (h, w), the output size will be matched to
            this. If size is an int, the smaller edge of the image will be matched to this number maintain the aspect
            ratio.
        :param how: the interpolation method. Valid values include `NEAREST`, `BILINEAR`, `BICUBIC`, and `LANCZOS`.
            Default is `BILINEAR`. Please refer to `PIL.Image` for detaisl.
        """
        super().__init__(*args, **kwargs)
        if isinstance(target_size, numbers.Number):
            self.output_dim = target_size
        else:
            raise ValueError('output_dim {} should be an integer'.format(target_size))
        self.how = how

    def craft(self, blob: 'np.ndarray', chunk_id: int, doc_id: int, *args, **kwargs) -> Dict:
        """
        Resize the image array to the given size.

        :param blob: the ndarray of the image
        :param chunk_id: the chunk id
        :param doc_id: the doc id
        :return: a chunk dict with the cropped image
        """
        raw_img = self.load_image(blob)
        _img = self._resize_short(raw_img, self.output_dim, self.how)
        img = self.restore_channel_axis(np.asarray(_img))
        return dict(
            doc_id=doc_id, offset=0, weight=1., blob=img.astype('float32'))
