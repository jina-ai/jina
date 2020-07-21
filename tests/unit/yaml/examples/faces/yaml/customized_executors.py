__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"


import numpy as np
from jina.executors.crafters.image import ImageChunkCrafter
from PIL import ImageOps


class ImageFlipper(ImageChunkCrafter):
    def craft(self, blob, doc_id, *args, **kwargs):
        raw_img = self.load_image(blob)
        _img = ImageOps.mirror(raw_img)
        img = self.restore_channel_axis(np.asarray(_img))
        return [{'doc_id': doc_id, 'blob': img.astype('float32')}, ]
