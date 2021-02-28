import numpy as np
import pytest
import pickle

from jina.excepts import UndefinedModel
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


def test_transform_encoder_train(caplog):
    train_data = np.random.rand(2, input_dim)
    with pytest.raises(UndefinedModel):
        encoder.train(train_data)

    encoder.logger.logger.propagate = True
    encoder.model = simple_model
    encoder.train(train_data)
    assert encoder.is_trained
    assert 'batch size' in caplog.text
    encoder.logger.logger.propagate = False


def test_transform_encoder_test():
    test_data = np.random.rand(10, input_dim)
    encoded_data = encoder.encode(test_data)
    assert encoded_data.shape == (test_data.shape[0], target_output_dim)
    assert type(encoded_data) == np.ndarray


def test__transform_encoder_model_path(tmpdir):
    with open(str(tmpdir)+'.pkl', 'wb') as output:
        pickle.dump(simple_model, output)
    encoder_path = TransformEncoder(model_path=str(tmpdir)+'.pkl', output_dim=target_output_dim)
    assert encoder_path.model
