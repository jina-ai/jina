from typing import TYPE_CHECKING

import tensorflow as tf

if TYPE_CHECKING:
    from tensorflow import Tensor
    import numpy


def _get_tf_device(device: str):
    return tf.device('/GPU:0') if device == 'cuda' else tf.device('/CPU:0')


def cosine(
    x_mat: 'Tensor', y_mat: 'Tensor', eps: float = 1e-7, device: str = 'cpu'
) -> 'numpy.ndarray':
    """Cosine distance between each row in x_mat and each row in y_mat.

    :param x_mat: np.ndarray with ndim=2
    :param y_mat: np.ndarray with ndim=2
    :param eps: a small jitter to avoid divde by zero
    :param device: the computational device for `embed_model`, can be either `cpu` or `cuda`.
    :return: np.ndarray  with ndim=2
    """
    with _get_tf_device(device):
        normalize_a = tf.nn.l2_normalize(x_mat, 1, epsilon=eps)
        normalize_b = tf.nn.l2_normalize(y_mat, 1, epsilon=eps)
        distance = 1 - tf.matmul(normalize_a, normalize_b, transpose_b=True)
        return distance.numpy()


def sqeuclidean(
    x_mat: 'Tensor', y_mat: 'Tensor', device: str = 'cpu'
) -> 'numpy.ndarray':
    """Squared euclidean distance between each row in x_mat and each row in y_mat.

    :param x_mat:  tensorflow array with ndim=2
    :param y_mat:  tensorflow array with ndim=2
    :param device: the computational device for `embed_model`, can be either `cpu` or `cuda`.
    :return: np.ndarray  with ndim=2
    """
    device = tf.device('/GPU:0') if device == 'cuda' else tf.device('/CPU:0')

    with _get_tf_device(device):
        return tf.reduce_sum(
            (tf.expand_dims(x_mat, 1) - tf.expand_dims(y_mat, 0)) ** 2, 2
        ).numpy()


def euclidean(x_mat: 'Tensor', y_mat: 'Tensor', device: str = 'cpu') -> 'numpy.ndarray':
    """Euclidean distance between each row in x_mat and each row in y_mat.

    :param x_mat:  tensorflow array with ndim=2
    :param y_mat:  tensorflow array with ndim=2
    :param device: the computational device for `embed_model`, can be either `cpu` or `cuda`.
    :return: np.ndarray  with ndim=2
    """
    device = tf.device('/GPU:0') if device == 'cuda' else tf.device('/CPU:0')

    with _get_tf_device(device):
        return tf.sqrt(
            tf.reduce_sum((tf.expand_dims(x_mat, 1) - tf.expand_dims(y_mat, 0)) ** 2, 2)
        ).numpy()
