import unittest

from jina.executors.crafters.image.normalize import ImageNormalizer
from tests.unit.executors.crafters.image import JinaImageTestCase


class MyTestCase(JinaImageTestCase):
    def test_transform_results(self):
        img_size = 217
        target_size = 224
        crafter = ImageNormalizer(target_size=target_size)
        img_array = self.create_random_img_array(img_size, img_size)
        crafted_chunk = crafter.craft(img_array, chunk_id=0, doc_id=0)
        self.assertEqual(crafted_chunk["blob"].shape, (224, 224, 3))


if __name__ == '__main__':
    unittest.main()
