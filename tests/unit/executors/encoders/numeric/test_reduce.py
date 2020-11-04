import numpy as np

from jina.executors.encoders.helper import reduce_max, reduce_mean, reduce_cls, reduce_min

test_data = np.array([[
    [10, 30, 10],
    [20, 20, 20],
    [30, 10, 30],
    [100, 100, 100]
], [
    [10, 30, 10],
    [20, 20, 20],
    [30, 10, 30],
    [100, 100, 100]
]]).astype('float32')

test_mask = np.array([
    [1, 1, 1, 0],
    [1, 1, 1, 1]
]).astype('float32')


def test_reduce_max():
    results = reduce_max(test_data, test_mask)
    for data, mask, result in zip(test_data, test_mask, results):
        num_valid_tokens = int(sum(mask))
        np.testing.assert_array_equal(data[:num_valid_tokens, :].max(axis=0), result)


def test_reduce_min():
    results = reduce_min(test_data, test_mask)
    for data, mask, result in zip(test_data, test_mask, results):
        num_valid_tokens = int(sum(mask))
        np.testing.assert_array_equal(data[:num_valid_tokens, :].min(axis=0), result)


def test_reduce_mean():
    results = reduce_mean(test_data, test_mask)
    for data, mask, result in zip(test_data, test_mask, results):
        num_valid_tokens = int(sum(mask))
        np.testing.assert_array_equal(data[:num_valid_tokens, :].mean(axis=0), result)


def test_reduce_cls_head():
    results = reduce_cls(test_data, test_mask, cls_pos='head')
    for data, mask, result in zip(test_data, test_mask, results):
        np.testing.assert_array_equal(data[0, :], result)


def test_reduce_cls_tail():
    results = reduce_cls(test_data, test_mask, cls_pos='tail')
    for data, mask, result in zip(test_data, test_mask, results):
        num_valid_tokens = int(sum(mask))
        np.testing.assert_array_equal(data[num_valid_tokens - 1, :], result)
