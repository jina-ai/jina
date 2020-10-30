import os

from jina.proto import jina_pb2

if False:
    import numpy as np


class BaseNdArray:
    """An abstract class for containing the protobuf message of NdArray. It defines interfaces
    for easier get/set value.

    Do not use this class directly. Subclass should be used.
    """

    def __init__(self, proto: 'jina_pb2._reflection.GeneratedProtocolMessageType' = None):
        """

        :param proto: the protobuf message, when not given then create a new one via :meth:`get_null_proto`
        """
        if proto:
            self.proto = proto  # a weak ref/copy
        else:
            self.proto = self.get_null_proto()

    def get_null_proto(self):
        """Get the new protobuf representation"""
        raise NotImplementedError

    @property
    def value(self):
        """Return the value of the ndarray, in numpy, scipy, tensorflow, pytorch format"""
        raise NotImplementedError

    @value.setter
    def value(self, value):
        """Set the value to protobuf"""
        raise NotImplementedError

    @property
    def is_sparse(self) -> bool:
        """Return true if the ndarray is sparse """
        raise NotImplementedError


class DenseNdArray(BaseNdArray):

    def __init__(self, proto: 'jina_pb2.DenseNdArray' = None, quantize: str = None):
        """

        :param proto: the protobuf message, when not given then create a new one
        :param quantize: the quantization method used when converting to protobuf.
            Availables are ``fp16``, ``uint8``, default is None.

        .. note::
            Remarks on quantization:
                The quantization only works when ``x`` is in ``float32`` or ``float64``. The motivation is to
                save the network bandwidth by using less bits to store the numpy array in the protobuf.

                    - ``fp16`` quantization is lossless, can be used widely. Each float is represented by 16 bits.
                    - ``uint8`` quantization is lossy. Each float is represented by 8 bits.
                    The algorithm behind is standard scaling.

                There is no need to specify the quantization type in :func:`pb2array`,
                as the quantize type is stored and the blob is self-contained to recover the original numpy array
        """
        super().__init__(proto)
        self.quantize = os.environ.get('JINA_ARRAY_QUANT', quantize)

    def get_null_proto(self):
        return jina_pb2.DenseNdArray()

    @property
    def value(self) -> 'np.ndarray':
        blob = self.proto
        x = np.frombuffer(blob.buffer, dtype=blob.dtype)

        if blob.quantization == jina_pb2.DenseNdArray.FP16:
            x = x.astype(blob.original_dtype)
        elif blob.quantization == jina_pb2.DenseNdArray.UINT8:
            x = x.astype(blob.original_dtype) * blob.scale + blob.min_val

        return x

    @value.setter
    def value(self, value: 'np.ndarray'):
        blob = self.proto
        x = value

        if self.quantize == 'fp16' and (x.dtype == np.float32 or x.dtype == np.float64):
            blob.quantization = jina_pb2.DenseNdArray.FP16
            blob.original_dtype = x.dtype.name
            x = x.astype(np.float16)
        elif self.quantize == 'uint8' and (x.dtype == np.float32 or x.dtype == np.float64 or x.dtype == np.float16):
            blob.quantization = jina_pb2.DenseNdArray.UINT8
            blob.max_val, blob.min_val = x.max(), x.min()
            blob.original_dtype = x.dtype.name
            blob.scale = (blob.max_val - blob.min_val) / 256
            x = ((x - blob.min_val) / blob.scale).astype(np.uint8)
        else:
            blob.quantization = jina_pb2.DenseNdArray.NONE

        blob.buffer = x.tobytes()
        blob.shape.extend(list(x.shape))
        blob.dtype = x.dtype.str

    @property
    def is_sparse(self) -> bool:
        return False
