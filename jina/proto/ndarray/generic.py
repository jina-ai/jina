from typing import Type

from . import BaseNdArray
from .dense import BaseDenseNdArray
from .dense.numpy import DenseNdArray
from .sparse import BaseSparseNdArray
from .sparse.scipy import SparseNdArray
from .. import jina_pb2


class GenericNdArray(BaseNdArray):
    """A generic view of the Protobuf NdArray, unifying the view of DenseNdArray and SparseNdArray

    This class should be used in nearly all the Jina context.

    Simple usage:

    .. highlight:: python
    .. code-block:: python

        # start from empty proto
        a = GenericNdArray()

        # start from an existig proto
        a = GenericNdArray(doc.embedding)

        # set value
        a.value = np.random.random([10, 5])

        # get value
        print(a.value)

        # set value to a TF sparse tensor
        a.is_sparse = True
        a.value = SparseTensor(...)
        print(a.value)

    Advanced usage:

    :class:`GenericNdArray` also takes a dense NdArray and a sparse NdArray constructor
    as arguments. You can consider them as the backend for dense and sparse NdArray. The combination
    is your choice, it could be:

    .. highlight:: python
    .. code-block:: python

        # numpy (dense) + scipy (sparse)
        from .dense.numpy import DenseNdArray
        from .sparse.scipy import SparseNdArray
        GenericNdArray(dense_cls=DenseNdArray, sparse_cls=SparseNdArray)

        # numpy (dense) + pytorch (sparse)
        from .dense.numpy import DenseNdArray
        from .sparse.pytorch import SparseNdArray
        GenericNdArray(dense_cls=DenseNdArray, sparse_cls=SparseNdArray)

        # numpy (dense) + tensorflow (sparse)
        from .dense.numpy import DenseNdArray
        from .sparse.tensorflow import SparseNdArray
        GenericNdArray(dense_cls=DenseNdArray, sparse_cls=SparseNdArray)

    Once you set `sparse_cls`, it will only accept the data type in that particular type.
    That is, you can not use a :class:`GenericNdArray` equipped with Tensorflow sparse to
    set/get Pytorch or Scipy sparse matrices.

    """

    def __init__(self, proto: 'jina_pb2.NdArray' = None,
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
        super().__init__(proto, *args, **kwargs)
        self.is_sparse = is_sparse
        self.dense_cls = dense_cls
        self.sparse_cls = sparse_cls
        self._args = args
        self._kwargs = kwargs

    def null_proto(self):
        return jina_pb2.NdArray()

    @property
    def value(self):
        stype = self.proto.WhichOneof('content')
        if stype == 'dense':
            return self.dense_cls(self.proto.dense).value
        elif stype == 'sparse':
            return self.sparse_cls(self.proto.sparse).value

    @value.setter
    def value(self, value):
        if self.is_sparse:
            self.sparse_cls(self.proto.sparse).value = value
        else:
            self.dense_cls(self.proto.dense).value = value
