import numpy as np
from jina.executors.crafters.image.crop import ImageCropper, CenterImageCropper
from tests.unit.executors.crafters.image import JinaImageTestCase


class ImageCropTestCase(JinaImageTestCase):
    def test_crop(self):
        img_size = 217
        img_array = self.create_random_img_array(img_size, img_size)
        left = 2
        top = 17
        width = 20
        height = 20
        crafter = ImageCropper(left, top, width, height)
        crafted_chunk = crafter.craft(img_array, 0, 0)
        np.testing.assert_array_equal(
            crafted_chunk['blob'], np.asarray(img_array[top:top + height, left:left + width, :]),
            'img_array: {}\ntest: {}\ncontrol:{}'.format(
                img_array.shape,
                crafted_chunk['blob'].shape,
                np.asarray(img_array[left:left + width, top:top + height, :]).shape))

    def test_center_crop(self):
        img_size = 217
        img_array = self.create_random_img_array(img_size, img_size)
        output_dim = 20
        crafter = CenterImageCropper(output_dim)
        crafted_chunk = crafter.craft(img_array, 0, 0)
        self.assertEqual(crafted_chunk["blob"].shape, (20, 20, 3))
