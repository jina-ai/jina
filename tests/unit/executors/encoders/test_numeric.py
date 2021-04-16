import numpy as np
import pickle

import pytest

from jina.executors.encoders.numeric import TransformEncoder

input_dim = 5
target_output_dim = 5


class SimpleModel:
    def fit(self, data):
        return data

    def transform(self, data):
        return data


@pytest.fixture()
def model_path(tmpdir):
    model_path = str(tmpdir) + '/model.pkl'
    model = SimpleModel()
    with open(model_path, 'wb') as output:
        pickle.dump(model, output)
    return model_path


@pytest.fixture()
def encoder(model_path):
    return TransformEncoder(model_path=model_path)


def test_transform_encoder_test(encoder):
    test_data = np.random.rand(10, input_dim)
    encoded_data = encoder.encode(test_data)
    assert encoded_data.shape == (test_data.shape[0], target_output_dim)
    assert type(encoded_data) == np.ndarray
