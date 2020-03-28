from typing import Tuple, Dict, List

import numpy as np
from PIL import Image

from .. import BaseSegmenter


class ImageNormalizer(BaseSegmenter):
    """:class:`ImageNormalizer` works on doc-level,
        it receives values of file names on the doc-level and returns image matrix on the chunk-level """

    def __init__(self,
                 output_dim,
                 img_mean: Tuple[float] = (0, 0, 0),
                 img_std: Tuple[float] = (1, 1, 1),
                 resize_dim: int = 256,
                 *args,
                 **kwargs):
        """
        :class:`ImageNormalizer` load an image file and craft into image matrix.

        :param output_dim: the output size. Both height and width are set to `output_dim`
        :param img_mean: the mean of the images in `RGB` channels. Set to `[0.485, 0.456, 0.406]` for the models trained
            on `imagenet` from `paddlehub`
        :param img_std: the std of the images in `RGB` channels. Set to `[0.229, 0.224, 0.225]` for the models trained
            on `imagenet` from `paddlehub`
        :param resize_dim: the size of images' height and width to resized to. The images are resized before cropping to
            the output size
        """
        super().__init__()
        self.output_dim = output_dim
        self.img_mean = np.array(img_mean).reshape((3, 1, 1))
        self.img_std = np.array(img_std).reshape((3, 1, 1))
        self.resize_dim = resize_dim

    def craft(self, raw_bytes, doc_id, *args, **kwargs) -> List[Dict]:
        """

        :param raw_bytes: the file name in bytes
        :param doc_id: the doc id
        :return: a list of chunks-level info represented by a dict
        """
        raw_img = Image.open(raw_bytes.decode())
        processed_img = self._normalize(raw_img)
        return [dict(doc_id=doc_id, offset=0, weight=1., blob=processed_img), ]

    def _normalize(self, img):
        img = self._resize_short(img, target_size=self.resize_dim)
        img = self._crop_image(img, target_size=self.output_dim, center=True)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img = np.array(img).astype('float32').transpose((2, 0, 1)) / 255
        img -= self.img_mean
        img /= self.img_std
        return img

    @staticmethod
    def _resize_short(img, target_size):
        percent = float(target_size) / min(img.size[0], img.size[1])
        resized_width = int(round(img.size[0] * percent))
        resized_height = int(round(img.size[1] * percent))
        img = img.resize((resized_width, resized_height), Image.LANCZOS)
        return img

    @staticmethod
    def _crop_image(img, target_size, center):
        width, height = img.size
        size = target_size
        if center:
            w_start = (width - size) / 2
            h_start = (height - size) / 2
        else:
            w_start = np.random.randint(0, width - size + 1)
            h_start = np.random.randint(0, height - size + 1)
        w_end = w_start + size
        h_end = h_start + size
        img = img.crop((w_start, h_start, w_end, h_end))
        return img
