from typing import Type

from . import BaseNdArray
from .dense import BaseDenseNdArray
from .dense.numpy import DenseNdArray
from .sparse import BaseSparseNdArray
from .sparse.scipy import SparseNdArray
from ...proto import jina_pb2

__all__ = ['NdArray']


class NdArray(BaseNdArray):
    """
    :class:`NdArray` is one of the **primitive data type** in Jina.

    It offers a Pythonic interface to allow users access and manipulate
    :class:`jina.jina_pb2.NdArrayProto` object without working with Protobuf itself.

    A generic view of the Protobuf NdArray, unifying the view of DenseNdArray and SparseNdArray

    This class should be used in nearly all the Jina context.

    Simple usage:

    .. highlight:: python
    .. code-block:: python

        # start from empty proto
        a = NdArray()

        # start from an existig proto
        a = NdArray(doc.embedding)

        # set value
        a.value = np.random.random([10, 5])

        # get value
        print(a.value)

        # set value to a TF sparse tensor
        a.is_sparse = True
        a.value = SparseTensor(...)
        print(a.value)

    Advanced usage:

    :class:`NdArray` also takes a dense NdArray and a sparse NdArray constructor
    as arguments. You can consider them as the backend for dense and sparse NdArray. The combination
    is your choice, it could be:

    .. highlight:: python
    .. code-block:: python

        # numpy (dense) + scipy (sparse)
        from .dense.numpy import DenseNdArray
        from .sparse.scipy import SparseNdArray
        NdArray(dense_cls=DenseNdArray, sparse_cls=SparseNdArray)

        # numpy (dense) + pytorch (sparse)
        from .dense.numpy import DenseNdArray
        from .sparse.pytorch import SparseNdArray
        NdArray(dense_cls=DenseNdArray, sparse_cls=SparseNdArray)

        # numpy (dense) + tensorflow (sparse)
        from .dense.numpy import DenseNdArray
        from .sparse.tensorflow import SparseNdArray
        NdArray(dense_cls=DenseNdArray, sparse_cls=SparseNdArray)

    Once you set `sparse_cls`, it will only accept the data type in that particular type.
    That is, you can not use a :class:`NdArray` equipped with Tensorflow sparse to
    set/get Pytorch or Scipy sparse matrices.

    """

    def __init__(self, proto: 'jina_pb2.NdArrayProto' = None,
                 is_sparse: bool = False,
                 dense_cls: Type['BaseDenseNdArray'] = DenseNdArray,
                 sparse_cls: Type['BaseSparseNdArray'] = SparseNdArray,
                 *args, **kwargs):
        """

        :param proto: the protobuf message, when not given then create a new one via :meth:`get_null_proto`
        :param is_sparse: if the ndarray is sparse, can be changed later
        :param dense_cls: the to-be-used class for DenseNdArray when `is_sparse=False`
        :param sparse_cls: the to-be-used class for SparseNdArray when `is_sparse=True`
        :param args:
        :param kwargs:
        """
        self.is_sparse = is_sparse
        self.dense_cls = dense_cls
        self.sparse_cls = sparse_cls
        super().__init__(proto, *args, **kwargs)
        self._args = args
        self._kwargs = kwargs

    def null_proto(self):
        """Get the new protobuf representation."""
        return jina_pb2.NdArrayProto()

    @property
    def value(self):
        """Get the value of protobuf and return in corresponding type."""
        stype = self._pb_body.WhichOneof('content')
        if stype == 'dense':
            return self.dense_cls(self._pb_body.dense).value
        elif stype == 'sparse':
            return self.sparse_cls(self._pb_body.sparse).value

    @value.setter
    def value(self, value):
        """Set the value of protobuf and with :param:`value`."""
        if self.is_sparse:
            self.sparse_cls(self._pb_body.sparse).value = value
        else:
            self.dense_cls(self._pb_body.dense).value = value

    def _build_content_dict(self):
        return {'value': self.value,
                'is_sparse': self.is_sparse}
