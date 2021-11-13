from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from torch import tensor
    import numpy


def cosine(
    x_mat: 'tensor', y_mat: 'tensor', eps: float = 1e-7, device: str = 'cpu'
) -> 'numpy.ndarray':
    """Cosine distance between each row in x_mat and each row in y_mat.

    :param x_mat: torch with ndim=2
    :param y_mat: torch with ndim=2
    :param eps: a small jitter to avoid divde by zero
    :param device: the computational device for `embed_model`, can be either `cpu` or `cuda`.
    :return: np.ndarray  with ndim=2
    """
    if device == 'cuda':
        x_mat = x_mat.cuda()
        y_mat = y_mat.cuda()

    a_n, b_n = x_mat.norm(dim=1)[:, None], y_mat.norm(dim=1)[:, None]
    a_norm = x_mat / torch.clamp(a_n, min=eps)
    b_norm = y_mat / torch.clamp(b_n, min=eps)
    sim_mt = 1 - torch.mm(a_norm, b_norm.transpose(0, 1))
    return sim_mt.cpu().detach().numpy()


def euclidean(x_mat: 'tensor', y_mat: 'tensor', device: str = 'cpu') -> 'numpy.ndarray':
    """Euclidean distance between each row in x_mat and each row in y_mat.

    :param x_mat:  torch array with ndim=2
    :param y_mat:  torch array with ndim=2
    :param device: the computational device for `embed_model`, can be either `cpu` or `cuda`.
    :return: np.ndarray  with ndim=2
    """
    if device == 'cuda':
        x_mat = x_mat.cuda()
        y_mat = y_mat.cuda()

    return torch.cdist(x_mat, y_mat).cpu().detach().numpy()


def sqeuclidean(
    x_mat: 'tensor', y_mat: 'tensor', device: str = 'cpu'
) -> 'numpy.ndarray':
    """Squared euclidean distance between each row in x_mat and each row in y_mat.

    :param x_mat:  torch array with ndim=2
    :param y_mat:  torch array with ndim=2
    :param device: the computational device for `embed_model`, can be either `cpu` or `cuda`.
    :return: np.ndarray  with ndim=2
    """
    if device == 'cuda':
        x_mat = x_mat.cuda()
        y_mat = y_mat.cuda()

    return (torch.cdist(x_mat, y_mat) ** 2).cpu().detach().numpy()
