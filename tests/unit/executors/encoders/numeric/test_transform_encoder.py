import pickle

import numpy as np

from jina.executors.encoders.numeric import TransformEncoder

input_dim = 28
target_output_dim = 2


def test_transform_encoder_train_and_encode(test_metas):
    train_data = np.random.rand(2000, input_dim)
    encoder = TransformEncoder(output_dim=target_output_dim, metas=test_metas)
    from sklearn.random_projection import GaussianRandomProjection
    encoder.model = GaussianRandomProjection(n_components=target_output_dim)
    encoder.train(train_data)
    test_data = np.random.rand(10, input_dim)
    encoded_data = encoder.encode(test_data)
    assert encoded_data.shape == (test_data.shape[0], target_output_dim)
    assert type(encoded_data) == np.ndarray


def test_transform_encoder_load_from_pickle(test_metas):
    train_data = np.random.rand(2000, input_dim)
    filename = 'transformer_model.model'
    from sklearn.random_projection import GaussianRandomProjection
    model = GaussianRandomProjection(n_components=target_output_dim)
    pickle.dump(model.fit(train_data), open(filename, 'wb'))
    encoder = TransformEncoder(model_path=filename, metas=test_metas)
    test_data = np.random.rand(10, input_dim)
    encoded_data = encoder.encode(test_data)
    transformed_data = model.transform(test_data)
    assert encoded_data.shape == (test_data.shape[0], target_output_dim)
    assert type(encoded_data) == np.ndarray
    np.testing.assert_almost_equal(encoded_data, transformed_data)
