from . import jina_pb2

_trigger_body_fields = set(kk
                           for v in [jina_pb2.Request.IndexRequest,
                                     jina_pb2.Request.SearchRequest,
                                     jina_pb2.Request.TrainRequest,
                                     jina_pb2.Request.ControlRequest] for kk in v.DESCRIPTOR.fields_by_name.keys())

_trigger_req_fields = set(jina_pb2.Request.DESCRIPTOR.fields_by_name.keys()).difference(
    {'train', 'index', 'search', 'control'})

_trigger_fields = _trigger_req_fields.union(_trigger_body_fields)


class LazyRequest:
    def __init__(self, request: bytes, is_compressed: bool):
        self._buffer = request
        self._deserialized = None
        self._is_compressed = is_compressed

    @property
    def is_used(self):
        return self._deserialized is not None

    def __getattr__(self, name: str):
        # https://docs.python.org/3/reference/datamodel.html#object.__getattr__
        if name in _trigger_fields:
            if self._deserialized is None:
                self._deserialized = jina_pb2.Request()
                if self._is_compressed:
                    import lz4.frame
                    _buffer = lz4.frame.decompress(self._buffer)
                else:
                    _buffer = self._buffer
                self._deserialized.ParseFromString(_buffer)
            if name in _trigger_body_fields:
                req = getattr(self._deserialized, self._deserialized.WhichOneof('body'))
                return getattr(req, name)
            elif name in _trigger_req_fields:
                return getattr(self._deserialized, name)
        raise AttributeError


class LazyMessage:

    def __init__(self, envelope: bytes, request: bytes):
        self._envelope_buffer = envelope
        self._request_buffer = request
