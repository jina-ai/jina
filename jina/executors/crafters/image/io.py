__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, List

import numpy as np

from .. import BaseSegmenter


class ImageReader(BaseSegmenter):
    """
    :class:`ImageReader` loads the image from the given file path and save the `ndarray` of the image in the Chunk.
    """

    def __init__(self, channel_axis: int = -1, *args, **kwargs):
        """
        :class:`ImageReader` load an image file and craft into image matrix.

        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        """
        super().__init__(*args, **kwargs)
        self.channel_axis = channel_axis

    def craft(self, raw_bytes: bytes, doc_id: int, *args, **kwargs) -> List[Dict]:
        """
        Read the image from the given file path that specified in `raw_bytes` and save the `ndarray` of the image in
            the `blob` of the chunk.

        :param raw_bytes: the image file path in raw bytes
        :param doc_id: the id of the Document

        """
        from PIL import Image
        raw_img = Image.open(raw_bytes.decode())
        if raw_img.mode != 'RGB':
            raw_img = raw_img.convert('RGB')
        img = np.array(raw_img).astype('float32')
        if self.channel_axis != -1:
            img = np.moveaxis(img, -1, self.channel_axis)
        return [dict(doc_id=doc_id, offset=0, weight=1., blob=img), ]
