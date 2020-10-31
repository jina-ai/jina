from ... import jina_pb2
from .. import BaseNdArray


class BaseDenseNdArray(BaseNdArray):

    def null_proto(self):
        return jina_pb2.DenseNdArray()
