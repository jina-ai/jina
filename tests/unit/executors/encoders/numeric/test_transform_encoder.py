import os
import pickle
import shutil

import numpy as np

from jina.executors.encoders.numeric import TransformEncoder

input_dim = 28
target_output_dim = 2


def rm_files(file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=False, onerror=None)


def test_transform_encoder_train_and_encode():
    train_data = np.random.rand(2000, input_dim)
    encoder = TransformEncoder(output_dim=target_output_dim)
    from sklearn.random_projection import GaussianRandomProjection
    encoder.model = GaussianRandomProjection(n_components=target_output_dim)
    encoder.train(train_data)
    test_data = np.random.rand(10, input_dim)
    encoded_data = encoder.encode(test_data)
    assert encoded_data.shape == (test_data.shape[0], target_output_dim)
    assert type(encoded_data) == np.ndarray

    rm_files([encoder.save_abspath, encoder.config_abspath])


def test_transform_encoder_load_from_pickle():
    train_data = np.random.rand(2000, input_dim)
    filename = 'transformer_model.model'
    from sklearn.random_projection import GaussianRandomProjection
    model = GaussianRandomProjection(n_components=target_output_dim)
    pickle.dump(model.fit(train_data), open(filename, 'wb'))
    encoder = TransformEncoder(model_path=filename)
    test_data = np.random.rand(10, input_dim)
    encoded_data = encoder.encode(test_data)
    transformed_data = model.transform(test_data)
    assert encoded_data.shape == (test_data.shape[0], target_output_dim)
    assert type(encoded_data) == np.ndarray
    np.testing.assert_almost_equal(encoded_data, transformed_data)
    rm_files([encoder.config_abspath, filename, encoder.save_abspath])
