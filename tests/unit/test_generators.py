import numpy as np

from jina.types.document.generators import from_ndarray

def test_from_ndarray():
    test_array = np.random.random((10, 64))
    # yield using from_ndarray along axis 0
    test_generator = from_ndarray(test_array)
    assert next(test_generator).blob.shape == np.array([64])

    # yield using from_ndarray along axis 1
    test_generator = from_ndarray(test_array, axis=1)
    assert next(test_generator).blob.shape == np.array([10])

    # yield using from_ndarray along axis 1, with shuffle
    test_generator = from_ndarray(test_array, axis=1, shuffle=True)
    assert next(test_generator).blob.shape == np.array([10])
