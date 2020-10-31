from ... import jina_pb2
from .. import BaseNdArray


class BaseDenseNdArray(BaseNdArray):
    """
    The base class for DenseNdArray.

    Do not use this class directly. Subclass should be used.
    """

    def null_proto(self):
        return jina_pb2.DenseNdArray()
