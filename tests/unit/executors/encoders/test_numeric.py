import numpy as np
import pytest

from jina.executors.encoders.numeric import TransformEncoder

input_dim = 5
target_output_dim = 5


class SimpleModel:
    def fit(self, data):
        return data

    def transform(self, data):
        return data


simple_model = SimpleModel()
encoder = TransformEncoder(output_dim=target_output_dim)


def test_transformencoder_train():
    train_data = np.random.rand(100, input_dim)
    encoder.model = simple_model
    encoder.train(train_data)
    assert encoder.train


def test_transformencoder_test():
    test_data = np.random.rand(10, input_dim)
    encoded_data = encoder.encode(test_data)
    assert encoded_data.shape == (test_data.shape[0], target_output_dim)
    assert type(encoded_data) == np.ndarray
