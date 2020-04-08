from typing import Tuple, Dict, List

import numpy as np

from . import ImageChunkCrafter


class ImageNormalizer(ImageChunkCrafter):
    """:class:`ImageNormalizer` works on doc-level,
        it receives values of file names on the doc-level and returns image matrix on the chunk-level """

    def __init__(self,
                 output_dim,
                 img_mean: Tuple[float] = (0, 0, 0),
                 img_std: Tuple[float] = (1, 1, 1),
                 resize_dim: int = 256,
                 channel_axis: int = -1,
                 *args,
                 **kwargs):
        """
        :class:`ImageNormalizer` normalize the image.

        :param output_dim: the output size. Both height and width are set to `output_dim`
        :param img_mean: the mean of the images in `RGB` channels. Set to `[0.485, 0.456, 0.406]` for the models trained
            on `imagenet` with pytorch backbone.
        :param img_std: the std of the images in `RGB` channels. Set to `[0.229, 0.224, 0.225]` for the models trained
            on `imagenet` with pytorch backbone.
        :param resize_dim: the size of images' height and width to resized to. The images are resized before cropping to
            the output size
        :param channel_axis: the axis id of the color channel, ``-1`` indicates the color channel info at the last axis
        """
        super().__init__(*args, **kwargs)
        self.output_dim = output_dim
        self.resize_dim = resize_dim
        self.channel_axis = channel_axis
        self.img_mean = np.array(img_mean).reshape((1, 1, 3))
        self.img_std = np.array(img_std).reshape((1, 1, 3))

    def craft(self, blob: 'np.ndarray', chunk_id: int, doc_id: int, *args, **kwargs) -> Dict:
        """

        :param blob: the ndarray of the image with the color channel at the last axis
        :param chunk_id: the chunk id
        :param doc_id: the doc id
        :return: a chunk dict with the normalized image
        """
        raw_img = self._load_image(blob)
        processed_img = self._normalize(raw_img)
        return dict(doc_id=doc_id, offset=0, weight=1., blob=processed_img)

    def _normalize(self, img):
        img = self._resize_short(img, target_size=self.resize_dim)
        img = self._crop_image(img, target_size=(self.output_dim, self.output_dim), how='center')
        img = np.array(img).astype('float32') / 255
        img -= self.img_mean
        img /= self.img_std
        if self.channel_axis != -1:
            img = np.moveaxis(img, -1, self.channel_axis)
        return img
