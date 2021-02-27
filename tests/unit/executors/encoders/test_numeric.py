import numpy as np

from jina.executors.encoders.numeric import TransformEncoder

input_dim = 28
target_output_dim = 2


def test_test_transformencoder():
    train_data = np.random.rand(100, input_dim)
    encoder = TransformEncoder(output_dim=target_output_dim)
    from sklearn.random_projection import SparseRandomProjection
    encoder.model = SparseRandomProjection(n_components=encoder.output_dim, random_state=encoder.random_state)
    encoder.train(train_data)

    test_data = np.random.rand(10, input_dim)
    encoded_data = encoder.encode(test_data)
    assert encoded_data.shape == (test_data.shape[0], target_output_dim)
    assert type(encoded_data) == np.ndarray
