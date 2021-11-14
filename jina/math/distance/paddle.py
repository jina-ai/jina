from typing import TYPE_CHECKING

import paddle

if TYPE_CHECKING:
    from paddle import tensor
    import numpy


def cosine(
    x_mat: 'tensor', y_mat: 'tensor', eps: float = 1e-7, device: str = 'cpu'
) -> 'numpy.ndarray':
    """Cosine distance between each row in x_mat and each row in y_mat.

    :param x_mat: np.ndarray with ndim=2
    :param y_mat: np.ndarray with ndim=2
    :param eps: a small jitter to avoid divde by zero
    :param device: the computational device for `embed_model`, can be either `cpu` or `cuda`.
    :return: np.ndarray  with ndim=2
    """
    paddle.set_device(device)

    a_n, b_n = x_mat.norm(axis=1)[:, None], y_mat.norm(axis=1)[:, None]
    a_norm = x_mat / paddle.clip(a_n, min=eps)
    b_norm = y_mat / paddle.clip(b_n, min=eps)
    sim_mt = 1 - paddle.mm(a_norm, b_norm.transpose(perm=[1, 0]))
    return sim_mt.numpy()


def sqeuclidean(
    x_mat: 'tensor', y_mat: 'tensor', device: str = 'cpu'
) -> 'numpy.ndarray':
    """Squared euclidean distance between each row in x_mat and each row in y_mat.

    :param x_mat:  paddle array with ndim=2
    :param y_mat:  paddle array with ndim=2
    :param device: the computational device for `embed_model`, can be either `cpu` or `cuda`.
    :return: np.ndarray  with ndim=2
    """
    paddle.set_device(device)

    return (
        paddle.sum(y_mat ** 2, axis=1)
        + paddle.sum(x_mat ** 2, axis=1)[:, None]
        - 2 * paddle.mm(x_mat, y_mat.transpose(perm=[1, 0]))
    ).numpy()


def euclidean(x_mat: 'tensor', y_mat: 'tensor', device: str = 'cpu') -> 'numpy.ndarray':
    """Euclidean distance between each row in x_mat and each row in y_mat.

    :param x_mat:  paddle array with ndim=2
    :param y_mat:  paddle array with ndim=2
    :param device: the computational device for `embed_model`, can be either `cpu` or `cuda`.
    :return: np.ndarray  with ndim=2
    """
    paddle.set_device(device)

    return paddle.sqrt(
        paddle.sum(y_mat ** 2, axis=1)
        + paddle.sum(x_mat ** 2, axis=1)[:, None]
        - 2 * paddle.mm(x_mat, y_mat.transpose(perm=[1, 0]))
    ).numpy()
