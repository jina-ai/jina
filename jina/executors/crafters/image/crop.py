from typing import Tuple, Dict, List

import numpy as np

from . import ImageChunkCrafter


class ImageCropper(ImageChunkCrafter):
    def __init__(self,
                 left: int,
                 top: int,
                 width: int,
                 height: int,
                 channel_axis: int = -1,
                 *args,
                 **kwargs):
        super().__init__(channel_axis, *args, **kwargs)
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.channel_axis = channel_axis

    def craft(self, blob: 'np.ndarray', chunk_id, doc_id, *args, **kwargs) -> Dict:
        """

        :param blob: the ndarray of the image with the color channel at the last axis
        :param chunk_id: the chunk id
        :param doc_id: the doc id
        :return: a chunk dict with the normalized image
        """
        raw_img = self._load_image(blob)
        processe_img = self._crop_image(raw_img, (self.width, self.height), self.left, self.top)
        return dict(doc_id=doc_id, offset=0, weight=1., blob=np.asarray(processe_img).astype('float32'))


class CenterImageCropper(ImageChunkCrafter):
    def __init__(self,
                 output_dim: int,
                 channel_axis: int = -1,
                 *args,
                 **kwargs):
        super().__init__(channel_axis, *args, **kwargs)
        self.output_dim = output_dim

    def craft(self, blob: 'np.ndarray', chunk_id, doc_id, *args, **kwargs) -> Dict:
        """

        :param blob: the ndarray of the image with the color channel at the last axis
        :param chunk_id: the chunk id
        :param doc_id: the doc id
        :return: a chunk dict with the normalized image
        """
        raw_img = self._load_image(blob)
        processe_img = self._crop_image(raw_img, (self.output_dim, self.output_dim), how='center')
        return dict(doc_id=doc_id, offset=0, weight=1., blob=np.asarray(processe_img).astype('float32'))


class RandomImageCropper(ImageChunkCrafter):
    def __init__(self,
                 output_dim: int,
                 num_patches: int = 1,
                 channel_axis: int = -1,
                 *args,
                 **kwargs):
        super().__init__(channel_axis, *args, **kwargs)
        self.output_dim = output_dim
        self.num_pathes = num_patches

    def craft(self, blob: 'np.ndarray', chunk_id, doc_id, *args, **kwargs) -> Dict:
        """

        :param blob: the ndarray of the image with the color channel at the last axis
        :param chunk_id: the chunk id
        :param doc_id: the doc id
        :return: a chunk dict with the normalized image
        """
        raw_img = self._load_image(blob)
        result = []
        for i in range(self.num_pathes):
            processe_img = self._crop_image(raw_img, (self.output_dim, self.output_dim), how='random')
            result.append(
                dict(doc_id=doc_id, offset=0, weight=1., blob=np.asarray(processe_img).astype('float32')))
        return result


class FiveImageCropper(ImageChunkCrafter):
    def __init__(self,
                 output_dim: int,
                 channel_axis: int = -1,
                 *args,
                 **kwargs):
        super().__init__(channel_axis, *args, **kwargs)
        self.output_dim = output_dim

    def craft(self, blob: 'np.ndarray', chunk_id, doc_id, *args, **kwargs) -> List[Dict]:
        """

        :param blob: the ndarray of the image with the color channel at the last axis
        :param chunk_id: the chunk id
        :param doc_id: the doc id
        :return: a chunk dict with the normalized image
        """
        raw_img = self._load_image(blob)
        image_width, image_height = raw_img.size
        crop_height = self.output_dim
        crop_width = self.output_dim
        if crop_width > image_width or crop_height > image_height:
            msg = "Requested crop size {} is bigger than input size {}"
            raise ValueError(msg.format(self.output_dim, (image_height, image_width)))

        tl = self._crop_image(raw_img, (crop_width, crop_height), 0, 0)
        tr = self._crop_image(raw_img, (image_width, crop_height), image_width - crop_width, 0)
        bl = self._crop_image(raw_img, (crop_width, image_height), 0, image_height - crop_height)
        br = self._crop_image(raw_img, (image_width, image_height),
                              image_width - crop_width, image_height - crop_height)
        center = self._crop_image(raw_img, (crop_height, crop_width), how='center')
        return [
            dict(doc_id=doc_id, offset=0, weight=1., blob=np.asarray(tl).astype('float32')),
            dict(doc_id=doc_id, offset=0, weight=1., blob=np.asarray(tr).astype('float32')),
            dict(doc_id=doc_id, offset=0, weight=1., blob=np.asarray(bl).astype('float32')),
            dict(doc_id=doc_id, offset=0, weight=1., blob=np.asarray(br).astype('float32')),
            dict(doc_id=doc_id, offset=0, weight=1., blob=np.asarray(center).astype('float32')),
            ]
