from typing import List

from . import jina_pb2

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
    def __init__(self, request: bytes, is_compressed: bool):
        self._buffer = request
        self._deserialized = None  # type: jina_pb2.Request
        self._is_compressed = is_compressed

    @property
    def is_used(self) -> bool:
        """Return True when request has been r/w at least once """
        return self._deserialized is not None

    def __getattr__(self, name: str):
        # https://docs.python.org/3/reference/datamodel.html#object.__getattr__
        if (name in _trigger_fields) or hasattr(_empty_request, name):
            if self._deserialized is None:
                self._deserialized = jina_pb2.Request()
                _buffer = self._buffer
                if self._is_compressed:
                    import lz4.frame
                    _buffer = lz4.frame.decompress(_buffer)
                self._deserialized.ParseFromString(_buffer)
        if name in _trigger_body_fields:
            req = getattr(self._deserialized, self._deserialized.WhichOneof('body'))
            return getattr(req, name)
        elif hasattr(_empty_request, name):
            return getattr(self._deserialized, name)
        else:
            raise AttributeError

    def dump(self):
        if self.is_used:
            return self._deserialized.SerializeToString()
        else:
            # no touch, skip serialization, return original
            return self._buffer


class LazyMessage:

    def __init__(self, envelope: bytes, request: bytes):
        self.envelope = jina_pb2.Envelope()
        self.envelope.ParseFromString(envelope)
        self.request = LazyRequest(request, False)

    def dump(self) -> List[bytes]:
        return [self.envelope.SerializeToString(), self.request.dump()]
