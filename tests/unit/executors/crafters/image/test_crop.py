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
        tmp_fn = os.path.join(cur_dir, 'test.jpeg')
        self.create_test_image(tmp_fn, size_width=1024, size_height=512)
        img = Image.open(tmp_fn)
        img = img.convert('RGB')
        width, height = img.size
        self.assertEqual(width, 1024)
        self.assertEqual(height, 512)
        half_width, half_height = int(width/2), int(height/2)
        img_array = np.array(img).astype('float32')
        crafter = ImageCropper(top=0, left=0, width=half_width, height=half_height)
        crafted_doc = crafter.craft(img_array)
        self.assertEqual(crafted_doc['blob'].shape, (half_height, half_width, 3))
        self.add_tmpfile(tmp_fn)

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
