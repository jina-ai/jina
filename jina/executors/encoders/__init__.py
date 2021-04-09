__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Any

from .. import BaseExecutor

if False:
    # fix type-hint complain for sphinx and flake
    from typing import TypeVar
    import numpy as np
    import scipy
    import tensorflow as tf
    import torch

    EncodingType = TypeVar(
        'EncodingType',
        np.ndarray,
        scipy.sparse.csr_matrix,
        scipy.sparse.coo_matrix,
        scipy.sparse.bsr_matrix,
        scipy.sparse.csc_matrix,
        torch.sparse_coo_tensor,
        tf.SparseTensor,
    )


class BaseEncoder(BaseExecutor):
    """``BaseEncoder`` encodes chunk into vector representation.

    The key function is :func:`encode`.

    .. seealso::
        :mod:`jina.drivers.encode`
    """

    def encode(self, data: Any, *args, **kwargs) -> 'EncodingType':
        """Encode the data, needs to be implemented in subclass.
        :param data: the data to be encoded
        :param args: additional positional arguments
        :param kwargs: additional key-value arguments
        """

        raise NotImplementedError


class BaseNumericEncoder(BaseEncoder):
    """BaseNumericEncoder encodes data from a ndarray, potentially B x ([T] x D) into a ndarray of B x D"""

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'EncodingType':
        """
        :param data: a `B x ([T] x D)` numpy ``ndarray``, `B` is the size of the batch
        :param args: additional positional arguments
        :param kwargs: additional key-value arguments
        """
        raise NotImplementedError


class BaseImageEncoder(BaseNumericEncoder):
    """BaseImageEncoder encodes data from a ndarray, potentially B x (Height x Width) into a ndarray of B x D"""

    pass


class BaseVideoEncoder(BaseNumericEncoder):
    """BaseVideoEncoder encodes data from a ndarray, potentially B x (Time x Height x Width) into a ndarray of B x D"""

    pass


class BaseAudioEncoder(BaseNumericEncoder):
    """BaseAudioEncoder encodes data from a ndarray, potentially B x (Time x D) into a ndarray of B x D"""

    pass


class BaseTextEncoder(BaseEncoder):
    """
    BaseTextEncoder encodes data from an array of string type (data.dtype.kind == 'U') of size B into a ndarray of B x D.
    """

    def encode(self, data: 'np.ndarray', *args, **kwargs) -> 'EncodingType':
        """

        :param data: an 1d array of string type (data.dtype.kind == 'U') in size B
        :param args: additional positional arguments
        :param kwargs: additional key-value arguments
        """
        raise NotImplementedError
