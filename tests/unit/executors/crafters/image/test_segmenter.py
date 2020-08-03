import numpy as np
from jina.executors.crafters.image.segmenter import RandomImageCropper, FiveImageCropper, \
    SlidingWindowImageCropper
from tests.unit.executors.crafters.image import JinaImageTestCase


class ImageSegmentTestCase(JinaImageTestCase):
    def test_random_crop(self):
        img_size = 217
        img_array = self.create_random_img_array(img_size, img_size)
        output_dim = 20
        num_pathes = 20
        crafter = RandomImageCropper(output_dim, num_pathes)
        crafted_chunk_list = crafter.craft(img_array, 0, 0)
        self.assertEqual(len(crafted_chunk_list), num_pathes)

    def test_random_crop(self):
        img_size = 217
        img_array = self.create_random_img_array(img_size, img_size)
        output_dim = 20
        crafter = FiveImageCropper(output_dim)
        crafted_chunk_list = crafter.craft(img_array, 0, 0)
        self.assertEqual(len(crafted_chunk_list), 5)

    def test_sliding_windows(self):
        img_size = 14
        img_array = self.create_random_img_array(img_size, img_size)
        output_dim = 4
        strides = (6, 6)
        crafter = SlidingWindowImageCropper(output_dim, strides, 'VALID')
        crafted_chunk_list = crafter.craft(img_array, 0, 0)
        self.assertEqual(len(crafted_chunk_list), 4)

        crafter = SlidingWindowImageCropper(output_dim, strides, 'SAME')
        crafted_chunk_list = crafter.craft(img_array, 0, 0)
        self.assertEqual(len(crafted_chunk_list), 9)
