import os
import numpy as np
from PIL import Image, ImageChops

from jina.executors.crafters.image.crop import ImageCropper, CenterImageCropper
from tests.unit.executors.crafters.image import JinaImageTestCase

cur_dir = os.path.dirname(os.path.abspath(__file__))


class ImageCropTestCase(JinaImageTestCase):
    def test_crop(self):
        img_size = 217
        img_array = self.create_random_img_array(img_size, img_size)
        left = 2
        top = 17
        width = 30
        height = 20
        crafter = ImageCropper(top=top, left=left, width=width, height=height)
        crafted_doc = crafter.craft(img_array)
        np.testing.assert_array_equal(
            crafted_doc['blob'], np.asarray(img_array[top:top + height, left:left + width, :]),
            'img_array: {}\ntest: {}\ncontrol:{}'.format(
                img_array.shape,
                crafted_doc['blob'].shape,
                np.asarray(img_array[left:left + width, top:top + height, :]).shape))
        crop = Image.fromarray(np.uint8(crafted_doc['blob']))
        crop_width, crop_height = crop.size
        self.assertEqual(crop_width, width)
        self.assertEqual(crop_height, height)
        self.assertEqual(crafted_doc['location'], (top, left))

    def test_crop_file_image(self):
        tmp_fn = os.path.join(cur_dir, 'imgs/cars.jpg')
        img = Image.open(tmp_fn).convert('RGB')
        img_array = np.array(img).astype('float32')
        crafter = ImageCropper(top=541, left=992, width=24, height=67)
        crafted_doc = crafter.craft(img_array)
        self.assertEqual(crafted_doc['blob'].shape, (67, 24, 3))
        crop_real_img = Image.open(os.path.join(cur_dir, 'imgs/faster_rcnn/person-0.png'))
        crop_real_img_array = np.array(crop_real_img).astype('float32')
        np.testing.assert_array_almost_equal(crafted_doc['blob'], crop_real_img_array)

    def test_center_crop(self):
        img_size = 217
        img_array = self.create_random_img_array(img_size, img_size)
        width = 30
        height = 20
        output_dim = (height, width)
        crafter = CenterImageCropper(output_dim)
        crafted_doc = crafter.craft(img_array)
        self.assertEqual(crafted_doc['blob'].shape, (height, width, 3))
        # int((img_size - output_dim) / 2)
        crop = Image.fromarray(np.uint8(crafted_doc['blob']))
        crop_width, crop_height = crop.size
        self.assertEqual(crop_width, width)
        self.assertEqual(crop_height, height)
        (top, left) = (98, 93)
        self.assertEqual(crafted_doc['location'], (top, left))
