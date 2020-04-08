import numbers
import numpy as np
from . import ImageChunkCrafter
from typing import Union, Tuple, List, Dict


class ImageResizer(ImageChunkCrafter):
    def __init__(self,
                 output_dim: int,
                 how='BILINEAR',
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(output_dim, numbers.Number):
            self.output_dim = output_dim
        else:
            raise ValueError('output_dim {} should be an integer'.format(output_dim))
        self.how = how

    def craft(self, blob: 'np.ndarray', chunk_id: int, doc_id: int, *args, **kwargs) -> Dict:
        raw_img = self._load_image(blob)
        processed_img = self._resize_short(raw_img, self.output_dim, self.how)
        return dict(
            doc_id=doc_id, offset=0, weight=1., blob=np.asarray(processed_img).astype('float32'))

