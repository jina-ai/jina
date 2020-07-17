import unittest

from jina.executors.crafters.image.resize import ImageResizer
from tests.unit.executors.crafters.image import JinaImageTestCase


class MyTestCase(JinaImageTestCase):
    def test_resize(self):
        img_width = 20
        img_height = 17
        output_dim = 71
        crafter = ImageResizer(target_size=output_dim)
        img_array = self.create_random_img_array(img_width, img_height)
        crafted_chunk = crafter.craft(img_array, chunk_id=0, doc_id=0)
        self.assertEqual(min(crafted_chunk['blob'].shape[:-1]), output_dim)


if __name__ == '__main__':
    unittest.main()
