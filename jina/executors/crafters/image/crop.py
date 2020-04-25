__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Tuple, Dict, List, Union

import numpy as np

from . import ImageChunkCrafter


class ImageCropper(ImageChunkCrafter):
    """
    :class:`ImageCropper` crops the image with the specific crop box. The coordinate is the same coordinate-system in
        the :py:mode:`PIL.Image`.
    """

    def __init__(self,
                 top: int,
                 left: int,
                 height: int,
                 width: int,
                 *args,
                 **kwargs):
        """

        :param top: the vertical coordinate of the top left corner of the crop box.
        :param left: the horizontal coordinate of the top left corner of the crop box.
        :param height: the height of the crop box.
        :param width: the width of the crop box.
        """
        super().__init__(*args, **kwargs)
        self.top = top
        self.left = left
        self.height = height
        self.width = width

    def craft(self, blob: 'np.ndarray', chunk_id, doc_id, *args, **kwargs) -> Dict:
        """
        Crop the input image array.

        :param blob: the ndarray of the image
        :param chunk_id: the chunk id
        :param doc_id: the doc id
        :returns: a chunk dict with the cropped image
        """
        raw_img = self.load_image(blob)
        _img = self._crop_image(raw_img, (self.width, self.height), self.left, self.top)
        img = self.restore_channel_axis(np.asarray(_img))
        return dict(doc_id=doc_id, offset=0, weight=1., blob=img.astype('float32'))


class CenterImageCropper(ImageChunkCrafter):
    """
    :class:`CenterImageCropper` crops the image with the center crop box. The coordinate is the same coordinate-system
        in the :py:mode:`PIL.Image`.
    """

    def __init__(self,
                 target_size: Union[Tuple[int], int],
                 *args,
                 **kwargs):
        """

        :param target_size: desired output size. If size is a sequence like (h, w), the output size will be matched to
            this. If size is an int, the output will have the same height and width as the `target_size`.
        """
        super().__init__(*args, **kwargs)
        self.target_size = target_size

    def craft(self, blob: 'np.ndarray', chunk_id: int, doc_id: int, *args, **kwargs) -> Dict:
        """
        Crop the input image array.

        :param blob: the ndarray of the image
        :param chunk_id: the chunk id
        :param doc_id: the doc id
        :return: a chunk dict with the cropped image
        """
        raw_img = self.load_image(blob)
        _img = self._crop_image(raw_img, self.target_size, how='center')
        img = self.restore_channel_axis(np.asarray(_img))
        return dict(doc_id=doc_id, offset=0, weight=1., blob=img.astype('float32'))


class RandomImageCropper(ImageChunkCrafter):
    """
    :class:`RandomImageCropper` crops the image with a random crop box. The coordinate is the same coordinate-system
        in the :py:mode:`PIL.Image`.
    """

    def __init__(self,
                 target_size: Union[Tuple[int], int],
                 num_patches: int = 1,
                 channel_axis: int = -1,
                 *args,
                 **kwargs):
        """

        :param target_size: desired output size. If size is a sequence like (h, w), the output size will be matched to
            this. If size is an int, the output will have the same height and width as the `target_size`.
        """
        super().__init__(channel_axis, *args, **kwargs)
        self.target_size = target_size
        self.num_pathes = num_patches

    def craft(self, blob: 'np.ndarray', chunk_id: int, doc_id: int, *args, **kwargs) -> List[Dict]:
        """
        Crop the input image array.

        :param blob: the ndarray of the image
        :param chunk_id: the chunk id
        :param doc_id: the doc id
        :return: a list of chunk dicts with the cropped images
        """
        raw_img = self.load_image(blob)
        result = []
        for i in range(self.num_pathes):
            _img = self._crop_image(raw_img, self.target_size, how='random')
            img = self.restore_channel_axis(np.asarray(_img))
            result.append(
                dict(doc_id=doc_id, offset=0, weight=1., blob=np.asarray(img).astype('float32')))
        return result


class FiveImageCropper(ImageChunkCrafter):
    """
    :class:`FiveImageCropper` crops the image into four corners and the central crop.
    """

    def __init__(self,
                 target_size: int,
                 *args,
                 **kwargs):
        """

        :param target_size: desired output size. If size is a sequence like (h, w), the output size will be matched to
            this. If size is an int, the output will have the same height and width as the `target_size`.
        """
        super().__init__(*args, **kwargs)
        self.target_size = target_size

    def craft(self, blob: 'np.ndarray', chunk_id: int, doc_id: int, *args, **kwargs) -> List[Dict]:
        """
        Crop the input image array.

        :param blob: the ndarray of the image with the color channel at the last axis
        :param chunk_id: the chunk id
        :param doc_id: the doc id
        :return: a list of five chunk dicts with the cropped images
        """
        raw_img = self.load_image(blob)
        image_width, image_height = raw_img.size
        if isinstance(self.target_size, int):
            target_h = target_w = self.target_size
        elif isinstance(self.target_size, Tuple) and len(self.target_size) == 2:
            target_h, target_w = self.target_size
        else:
            raise ValueError('target_size should be an integer or a tuple of two integers: {}'.format(self.target_size))
        _tl = self._crop_image(raw_img, self.target_size, 0, 0)
        tl = self.restore_channel_axis(np.asarray(_tl))
        _tr = self._crop_image(raw_img, self.target_size, image_width - target_w, 0)
        tr = self.restore_channel_axis(np.asarray(_tr))
        _bl = self._crop_image(raw_img, self.target_size, 0, image_height - target_h)
        bl = self.restore_channel_axis(np.asarray(_bl))
        _br = self._crop_image(raw_img, self.target_size, image_width - target_w, image_height - target_h)
        br = self.restore_channel_axis(np.asarray(_br))
        _center = self._crop_image(raw_img, self.target_size, how='center')
        center = self.restore_channel_axis(np.asarray(_center))
        return [
            dict(doc_id=doc_id, offset=0, weight=1., blob=tl.astype('float32')),
            dict(doc_id=doc_id, offset=0, weight=1., blob=tr.astype('float32')),
            dict(doc_id=doc_id, offset=0, weight=1., blob=bl.astype('float32')),
            dict(doc_id=doc_id, offset=0, weight=1., blob=br.astype('float32')),
            dict(doc_id=doc_id, offset=0, weight=1., blob=center.astype('float32')),
        ]


class SlidingWindowImageCropper(ImageChunkCrafter):
    """
    :class:`SlidingWindowImageCropper` crops the image with a sliding window.
    """

    def __init__(self,
                 target_size: int,
                 strides: Tuple[int],
                 padding='VALID',
                 *args,
                 **kwargs):
        """

        :param target_size: desired output size. If size is a sequence like (h, w), the output size will be matched to
            this. If size is an int, the output will have the same height and width as the `target_size`.
        :param strides: the strides between two neighboring sliding windows. `strides` is a sequence like (h, w), in
            which denote the strides on the vertical and the horizontal axis.
        :param padding: If `VALID`, only patches which are fully contained in the input image are included. If `SAME`,
            all patches whose starting point is inside the input are included, and areas outside the input default to
            zero. The `padding` argument has no effect on the size of each patch, it determines how many patches are
            extracted. Default is `VALID`.
        """
        super().__init__(*args, **kwargs)
        self.target_size = target_size
        if len(strides) != 2:
            raise ValueError('strides should be a tuple of two integers: {}'.format(strides))
        self.stride_h, self.stride_w = strides
        self.padding = padding

    def craft(self, blob: 'np.ndarray', chunk_id, doc_id, *args, **kwargs) -> List[Dict]:
        """
        Crop the input image array with a sliding window.

        :param blob: the ndarray of the image with the color channel at the last axis
        :param chunk_id: the chunk id
        :param doc_id: the doc id
        :return: a list of chunk dicts with the cropped images.
        """
        raw_img = np.copy(blob)
        raw_img = self.check_channel_axis(raw_img)
        if self.padding == 'SAME':
            raw_img = self._expand_img(blob)
        h, w, c = raw_img.shape
        row_step = raw_img.strides[0]
        col_step = raw_img.strides[1]
        expanded_img = np.lib.stride_tricks.as_strided(
            raw_img,
            (
                1 + int((h - self.target_size) / self.stride_h),
                1 + int((w - self.target_size) / self.stride_w),
                self.target_size,
                self.target_size,
                c
            ), (
                row_step * self.stride_h,
                col_step * self.stride_w,
                row_step,
                col_step,
                1))
        expanded_img = expanded_img.reshape((-1, self.target_size, self.target_size, c))
        results = []
        for _blob in expanded_img:
            blob = self.restore_channel_axis(_blob)
            results.append(dict(doc_id=doc_id, offset=0, weight=1.0, blob=blob.astype('float32')))
        return results

    def _expand_img(self, img: 'np.ndarray') -> 'np.ndarray':
        h, w, c = img.shape
        ext_h = self.target_size - h % self.stride_h
        ext_w = self.target_size - w % self.stride_w
        return np.pad(img,
                      ((0, ext_h), (0, ext_w), (0, 0)),
                      mode='constant',
                      constant_values=0)
