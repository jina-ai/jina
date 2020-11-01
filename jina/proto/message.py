import os
import sys
from typing import List, Union

from . import jina_pb2
from ..excepts import MismatchedVersion

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
    def __init__(self, request: bytes, compress: 'jina_pb2.Envelope.CompressAlgo'):
        self._buffer = request
        self._deserialized = None  # type: jina_pb2.Request
        self._compress = compress
        self._size = sys.getsizeof(self._buffer)

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
                if self._compress == jina_pb2.Envelope.LZ4:
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

    def SerializeToString(self):
        if self.is_used:
            _buffer = self._deserialized.SerializeToString()
            if self._compress == jina_pb2.Envelope.LZ4:
                import lz4.frame
                _buffer = lz4.frame.compress(_buffer)
            self._size = sys.getsizeof(_buffer)
            return _buffer
        else:
            # no touch, skip serialization, return original
            return self._buffer

    @property
    def size(self) -> int:
        """Get the size in bytes.

        To get the latest size, use it after :meth:`dump`
        """
        return self._size


class LazyMessage:

    def __init__(self, envelope: Union[bytes, 'jina_pb2.Envelope'], request: Union[bytes, 'jina_pb2.Request'], check_version: bool = False):
        if isinstance(envelope, bytes):
            self.envelope = jina_pb2.Envelope()
            self.envelope.ParseFromString(envelope)
        else:
            self.envelope = envelope
        self.request = LazyRequest(request, self.envelope.compress)
        self._size = sys.getsizeof(request) + sys.getsizeof(envelope)
        if check_version:
            self.check_version()

    def SerializeToString(self) -> List[bytes]:
        r1 = self.envelope.SerializeToString()
        r2 = self.request.SerializeToString()
        self._size = sys.getsizeof(r1) + sys.getsizeof(r2)
        return [r1, r2]

    @property
    def size(self) -> int:
        """Get the size in bytes.

        To get the latest size, use it after :meth:`dump`
        """
        return self._size

    def check_version(self):
        from ..logging import default_logger
        from .. import __version__, __proto_version__
        if hasattr(self.envelope, 'version'):
            if not self.envelope.version.jina:
                # only happen in unittest
                default_logger.warning('incoming message contains empty "version.jina", '
                                       'you may ignore it in debug/unittest mode. '
                                       'otherwise please check if gateway service set correct version')
            elif __version__ != self.envelope.version.jina:
                raise MismatchedVersion('mismatched JINA version! '
                                        'incoming message has JINA version %s, whereas local JINA version %s' % (
                                            self.envelope.version.jina, __version__))

            if not self.envelope.version.proto:
                # only happen in unittest
                default_logger.warning('incoming message contains empty "version.proto", '
                                       'you may ignore it in debug/unittest mode. '
                                       'otherwise please check if gateway service set correct version')
            elif __proto_version__ != self.envelope.version.proto:
                raise MismatchedVersion('mismatched protobuf version! '
                                        'incoming message has protobuf version %s, whereas local protobuf version %s' % (
                                            self.envelope.version.proto, __proto_version__))

            if not self.envelope.version.vcs or not os.environ.get('JINA_VCS_VERSION'):
                default_logger.warning('incoming message contains empty "version.vcs", '
                                       'you may ignore it in debug/unittest mode, '
                                       'or if you run jina OUTSIDE docker container where JINA_VCS_VERSION is unset'
                                       'otherwise please check if gateway service set correct version')
            elif os.environ.get('JINA_VCS_VERSION') != self.envelope.version.vcs:
                raise MismatchedVersion('mismatched vcs version! '
                                        'incoming message has vcs_version %s, whereas local environment vcs_version is %s' % (
                                            self.envelope.version.vcs, os.environ.get('JINA_VCS_VERSION')))

        else:
            raise MismatchedVersion('version_check=True locally, '
                                    'but incoming message contains no version info in its envelope. '
                                    'the message is probably sent from a very outdated JINA version')
