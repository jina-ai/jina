from jina.executors.crafters.image.normalize import ImageNormalizer
from tests.unit.executors.crafters.image import JinaImageTestCase


class ImageNormalizerTestCase(JinaImageTestCase):
    def test_transform_results(self):
        img_size = 217
        target_size = 224
        crafter = ImageNormalizer(target_size=target_size)
        img_array = self.create_random_img_array(img_size, img_size)
        crafted_doc = crafter.craft(img_array)
        self.assertEqual(crafted_doc["blob"].shape, (224, 224, 3))
