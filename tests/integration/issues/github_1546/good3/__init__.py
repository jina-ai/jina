from typing import Tuple, Dict, List, Union

import numpy as np
from jina.executors.segmenters import BaseSegmenter

from .helper import _crop_image, _move_channel_axis, _load_image


class FiveImageCropper2(BaseSegmenter):
    """
    :class:`FiveImageCropper` crops the image into four corners and the central crop.
    """

    def __init__(
        self,
        target_size: Union[Tuple[int, int], int] = 224,
        channel_axis: int = -1,
        *args,
        **kwargs,
    ):
        """

        :param target_size: desired output size. If size is a sequence like (h, w), the output size will be matched to
            this. If size is an int, the output will have the same height and width as the `target_size`.
        """
        super().__init__(*args, **kwargs)
        self.target_size = target_size
        self.channel_axis = channel_axis

    def segment(self, blob: 'np.ndarray', *args, **kwargs) -> List[Dict]:
        """
        Crop the input image array.

        :param blob: the ndarray of the image with the color channel at the last axis
        :return: a list of five chunk dicts with the cropped images
        """
        raw_img = _load_image(blob, self.channel_axis)
        image_width, image_height = raw_img.size
        if isinstance(self.target_size, int):
            target_h = target_w = self.target_size
        elif isinstance(self.target_size, Tuple) and len(self.target_size) == 2:
            target_h, target_w = self.target_size
        else:
            raise ValueError(
                f'target_size should be an integer or a tuple of two integers: {self.target_size}'
            )
        _tl, top_tl, left_tl = _crop_image(raw_img, self.target_size, 0, 0)
        tl = _move_channel_axis(np.asarray(_tl), -1, self.channel_axis)
        _tr, top_tr, left_tr = _crop_image(
            raw_img, self.target_size, top=0, left=image_width - target_w
        )
        tr = _move_channel_axis(np.asarray(_tr), -1, self.channel_axis)
        _bl, top_bl, left_bl = _crop_image(
            raw_img, self.target_size, top=image_height - target_h, left=0
        )
        bl = _move_channel_axis(np.asarray(_bl), -1, self.channel_axis)
        _br, top_br, left_br = _crop_image(
            raw_img,
            self.target_size,
            top=image_height - target_h,
            left=image_width - target_w,
        )
        br = _move_channel_axis(np.asarray(_br), -1, self.channel_axis)
        _center, top_center, left_center = _crop_image(
            raw_img, self.target_size, how='center'
        )
        center = _move_channel_axis(np.asarray(_center), -1, self.channel_axis)
        return [
            dict(
                offset=0,
                weight=1.0,
                blob=tl.astype('float32'),
                location=(top_tl, left_tl),
            ),
            dict(
                offset=0,
                weight=1.0,
                blob=tr.astype('float32'),
                location=(top_tr, left_tr),
            ),
            dict(
                offset=0,
                weight=1.0,
                blob=bl.astype('float32'),
                location=(top_bl, left_bl),
            ),
            dict(
                offset=0,
                weight=1.0,
                blob=br.astype('float32'),
                location=(top_br, left_br),
            ),
            dict(
                offset=0,
                weight=1.0,
                blob=center.astype('float32'),
                location=(top_center, left_center),
            ),
        ]
