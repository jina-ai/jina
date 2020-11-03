from typing import Optional

from .. import jina_pb2
from ...enums import CompressAlgo

_trigger_body_fields = set(kk
                           for v in [jina_pb2.Request.IndexRequest,
                                     jina_pb2.Request.SearchRequest,
                                     jina_pb2.Request.TrainRequest,
                                     jina_pb2.Request.ControlRequest]
                           for kk in v.DESCRIPTOR.fields_by_name.keys())
_trigger_req_fields = set(jina_pb2.Request.DESCRIPTOR.fields_by_name.keys()).difference(
    {'train', 'index', 'search', 'control'})
_trigger_fields = _trigger_req_fields.union(_trigger_body_fields)
_empty_request = jina_pb2.Request()


class LazyRequest:
    """
    A container for serialized :class:`jina_pb2.Request` that only triggers deserialization
    and decompression when receives the first read access to its member.

    It overrides :meth:`__getattr__` to provide the same get/set interface as an
    :class:`jina_pb2.Request` object.

    """

    def __init__(self, request: bytes, envelope: Optional['jina_pb2.Envelope'] = None):
        self._buffer = request
        self._deserialized = None  # type: jina_pb2.Request
        self._envelope = envelope

    @property
    def is_used(self) -> bool:
        """Return True when request has been r/w at least once """
        return self._deserialized is not None

    def __getattr__(self, name: str):
        # https://docs.python.org/3/reference/datamodel.html#object.__getattr__
        if (name in _trigger_fields) or hasattr(_empty_request, name):
            self._deserialized = self.as_pb_object()
        if name in _trigger_body_fields:
            req = getattr(self._deserialized, self._deserialized.WhichOneof('body'))
            return getattr(req, name)
        elif hasattr(_empty_request, name):
            return getattr(self._deserialized, name)
        else:
            raise AttributeError

    def _decompress(self, data: bytes) -> bytes:
        if not self._envelope.compression.algorithm:
            return data

        ctag = CompressAlgo.from_string(self._envelope.compression.algorithm)
        if ctag == CompressAlgo.LZ4:
            import lz4.frame
            data = lz4.frame.decompress(data)
        elif ctag == CompressAlgo.BZ2:
            import bz2
            data = bz2.decompress(data)
        elif ctag == CompressAlgo.LZMA:
            import lzma
            data = lzma.decompress(data)
        elif ctag == CompressAlgo.ZLIB:
            import zlib
            data = zlib.decompress(data)
        elif ctag == CompressAlgo.GZIP:
            import gzip
            data = gzip.decompress(data)
        return data

    def as_pb_object(self) -> 'jina_pb2.Request':
        if self._deserialized is None:
            r = jina_pb2.Request()
            _buffer = self._decompress(self._buffer)
            r.ParseFromString(_buffer)
            self._deserialized = r

            # # Though I can modify back the envelope, not sure if it is a good design:
            # # My intuition is: if the content is changed dramatically, e.g. fron index to control request,
            # # then whatever writes on the envelope should be dropped
            # # depreciated. The only reason to reuse the envelope is saving cost on Envelope(), which is
            # # really a minor minor (and evil) optimization.
            # if self._envelope:
            #     self._envelope.request_type = getattr(r, r.WhichOneof('body')).__class__.__name__

            return r
        else:
            return self._deserialized

    def SerializeToString(self):
        if self.is_used:
            return self._deserialized.SerializeToString()
        else:
            # no touch, skip serialization, return original
            return self._buffer
