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

    def __init__(self, channel_axis: int = -1, *args, **kwargs):
        """
        :class:`ImageReader` load an image file and craft into image matrix.

        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        """
        super().__init__(*args, **kwargs)
        self.channel_axis = channel_axis

    def craft(self, buffer: bytes, uri: str, doc_id: int, *args, **kwargs) -> List[Dict]:
        """
        Read the image from the given file path that specified in `buffer` and save the `ndarray` of the image in
            the `blob` of the chunk.

        :param buffer: the image in raw bytes
        :param uri: the image file path
        :param doc_id: the id of the Document

        """
        from PIL import Image
        if buffer:
            raw_img = Image.open(io.BytesIO(buffer))
        elif uri:
            raw_img = Image.open(uri)
        else:
            raise ValueError('no value found in "buffer" and "uri"')
        raw_img = raw_img.convert('RGB')
        img = np.array(raw_img).astype('float32')
        if self.channel_axis != -1:
            img = np.moveaxis(img, -1, self.channel_axis)
        return [dict(offset=0, weight=1., blob=img)]
