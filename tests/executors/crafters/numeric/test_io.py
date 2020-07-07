import unittest

import numpy as np
from jina.executors.crafters.numeric.io import ArrayStringReader, ArrayBytesReader
from tests import JinaTestCase


class MyTestCase(JinaTestCase):
    def test_array_reader(self):
        size = 8
        sample_array = np.random.rand(size).astype('float32')
        text = ','.join([str(x) for x in sample_array])

        reader = ArrayStringReader()
        crafted_doc = reader.craft(text, 0)

        self.assertEqual(crafted_doc['blob'].shape[0], size)
        np.testing.assert_array_equal(crafted_doc['blob'], sample_array)

    def test_bytes_reader(self):
        size = 8
        sample_array = np.random.rand(size).astype('float32')
        array_bytes = sample_array.tobytes()

        reader = ArrayBytesReader()
        crafted_doc = reader.craft(array_bytes, 0)

        self.assertEqual(crafted_doc['blob'].shape[0], size)
        np.testing.assert_array_equal(crafted_doc['blob'], sample_array)

    def test_bytes_reader_int_type(self):
        size = 8
        sample_array = np.random.rand(size).astype('int')
        array_bytes = sample_array.tobytes()

        reader = ArrayBytesReader(as_type='int')
        crafted_doc = reader.craft(array_bytes, 0)

        self.assertEqual(crafted_doc['blob'].shape[0], size)
        np.testing.assert_array_equal(crafted_doc['blob'], sample_array)

    def test_bytes_reader_wrong_type(self):
        size = 8
        sample_array = np.random.rand(size).astype('float32')
        array_bytes = sample_array.tobytes()

        reader = ArrayBytesReader(as_type='float64')
        crafted_doc = reader.craft(array_bytes, 0)

        self.assertEqual(crafted_doc['blob'].shape[0], size / 2)


if __name__ == '__main__':
    unittest.main()
