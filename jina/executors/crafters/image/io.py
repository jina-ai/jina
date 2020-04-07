from typing import Tuple, Dict, List

import numpy as np

from .. import BaseSegmenter


class ImageReader(BaseSegmenter):
    def __init__(self, channel_axis: int = -1, *args, **kwargs):
        """
        :class:`ImageReader` load an image file and craft into image matrix.

        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        """
        super().__init__(*args, **kwargs)
        self.channel_axis = channel_axis

    def craft(self, raw_bytes, doc_id, *args, **kwargs) -> List[Dict]:
        from PIL import Image
        raw_img = Image.open(raw_bytes.decode())
        raw_img.tobytes()
        if raw_img.mode != 'RGB':
            raw_img = raw_img.convert('RGB')
        img = np.array(raw_img).astype('float32')
        if self.channel_axis != -1:
            img = np.moveaxis(img, -1, self.channel_axis)
        return [dict(doc_id=doc_id, offset=0, weight=1., blob=img), ]
