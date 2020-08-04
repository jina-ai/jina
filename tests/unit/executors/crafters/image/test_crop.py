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
        crafter = ImageCropper(top=top, left=left, width=width, height=height)
        crafted_doc = crafter.craft(img_array)
        np.testing.assert_array_equal(
            crafted_doc['blob'], np.asarray(img_array[top:top + height, left:left + width, :]),
            'img_array: {}\ntest: {}\ncontrol:{}'.format(
                img_array.shape,
                crafted_doc['blob'].shape,
                np.asarray(img_array[left:left + width, top:top + height, :]).shape))
        self.assertEqual(crafted_doc['location'], (top, left))

    def test_center_crop(self):
        img_size = 217
        img_array = self.create_random_img_array(img_size, img_size)
        output_dim = 20
        crafter = CenterImageCropper(output_dim)
        crafted_doc = crafter.craft(img_array)
        self.assertEqual(crafted_doc['blob'].shape, (20, 20, 3))
        # int((img_size - output_dim) / 2)
        (top, left) = (98, 98)
        self.assertEqual(crafted_doc['location'], (top, left))
