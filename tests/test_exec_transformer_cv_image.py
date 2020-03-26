import os
import unittest

from jina.executors.transformers.cv.image import ImageNormalizer
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    @unittest.skipUnless('JINA_TEST_PRETRAINED' in os.environ, 'skip the pretrained test if not set')
    def test_transform_results(self):
        transformer = ImageNormalizer(output_dim=224)
        tmp_fn = os.path.join(transformer.current_workspace, "test.jpeg")
        self.create_test_image(tmp_fn)
        test_chunk, *_ = transformer.transform(tmp_fn.encode("utf8"), doc_id=0)
        self.assertEqual(test_chunk["blob"].shape, (3, 224, 224))
        self.add_tmpfile(tmp_fn)

    @staticmethod
    def create_test_image(output_fn):
        from PIL import Image
        image = Image.new('RGB', size=(50, 50), color=(155, 0, 0))
        with open(output_fn, "wb") as f:
            image.save(f, 'jpeg')


if __name__ == '__main__':
    unittest.main()
