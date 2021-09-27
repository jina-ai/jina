from .. import BaseNdArray
from ....proto import jina_pb2

__all__ = ['BaseDenseNdArray']


class BaseDenseNdArray(BaseNdArray):
    """
    The base class for DenseNdArray.

    Do not use this class directly. Subclass should be used.
    """

    def __init__(self, *args, **kwargs):
        """Set constructor method."""
        super().__init__(*args, **kwargs)
        self.is_sparse = False

    def null_proto(self):
        """Get the new protobuf representation."""
        return jina_pb2.DenseNdArrayProto()
