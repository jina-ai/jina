import os
import unittest

from jina.executors.crafters.image.io import ImageReader
from . import JinaImageTestCase


class MyTestCase(JinaImageTestCase):
    def test_io(self):
        crafter = ImageReader()
        tmp_fn = os.path.join(crafter.current_workspace, "test.jpeg")
        img_size = 50
        self.create_test_image(tmp_fn, size=img_size)
        test_chunk, *_ = crafter.craft(tmp_fn.encode("utf8"), doc_id=0)
        self.assertEqual(test_chunk["blob"].shape, (img_size, img_size, 3))
        self.add_tmpfile(tmp_fn)


if __name__ == '__main__':
    unittest.main()
