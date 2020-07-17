import os
import unittest
import io
from PIL import Image

from jina.executors.crafters.image.io import ImageReader
from tests.unit.executors.crafters.image import JinaImageTestCase


class MyTestCase(JinaImageTestCase):
    def test_io_uri(self):
        crafter = ImageReader()
        tmp_fn = os.path.join(crafter.current_workspace, 'test.jpeg')
        img_size = 50
        self.create_test_image(tmp_fn, size=img_size)
        test_doc = crafter.craft(buffer=None, uri=tmp_fn, doc_id=0)
        self.assertEqual(test_doc['blob'].shape, (img_size, img_size, 3))
        self.add_tmpfile(tmp_fn)

    def test_io_buffer(self):
        crafter = ImageReader()
        tmp_fn = os.path.join(crafter.current_workspace, 'test.jpeg')
        img_size = 50
        self.create_test_image(tmp_fn, size=img_size)
        image_buffer = io.BytesIO()
        img = Image.open(tmp_fn)
        img.save(image_buffer, format='PNG')
        image_buffer.seek(0)
        test_doc = crafter.craft(buffer=image_buffer.getvalue(), uri=None, doc_id=0)
        self.assertEqual(test_doc['blob'].shape, (img_size, img_size, 3))
        self.add_tmpfile(tmp_fn)


if __name__ == '__main__':
    unittest.main()
