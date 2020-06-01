__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import io
from typing import Dict, List

import numpy as np

from .. import BaseSegmenter


class ImageReader(BaseSegmenter):
    """
    :class:`ImageReader` loads the image from the given file path and save the `ndarray` of the image in the Chunk.
    """

    def __init__(self, channel_axis: int = -1, from_bytes: bool = False, *args, **kwargs):
        """
        :class:`ImageReader` load an image file and craft into image matrix.

        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        :param from_bytes: if set to true, then load image directly from buffer, otherwise it assumes buffer as file path
        """
        super().__init__(*args, **kwargs)
        self.channel_axis = channel_axis
        self.from_bytes = from_bytes

    def craft(self, buffer: bytes, uri: str, doc_id: int, *args, **kwargs) -> List[Dict]:
        """
        Read the image from the given file path that specified in `buffer` and save the `ndarray` of the image in
            the `blob` of the chunk.

        :param buffer: the image in raw bytes
        :param uri: the image file path
        :param doc_id: the id of the Document

        """
        from PIL import Image
        if self.from_bytes:
            raw_img = Image.open(io.BytesIO(buffer))
        else:
            raw_img = Image.open(uri)
        if raw_img.mode != 'RGB':
            raw_img = raw_img.convert('RGB')
        img = np.array(raw_img).astype('float32')
        if self.channel_axis != -1:
            img = np.moveaxis(img, -1, self.channel_axis)
        return [dict(doc_id=doc_id, offset=0, weight=1., blob=img), ]
