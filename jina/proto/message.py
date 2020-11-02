import os
import sys
from typing import List, Union, Optional

from . import jina_pb2
from .. import __version__, __proto_version__
from ..excepts import MismatchedVersion
from ..logging import default_logger

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
    def __init__(self, request: bytes, envelope: Optional['jina_pb2.Envelope'] = None):
        self._buffer = request
        self._deserialized = None  # type: jina_pb2.Request
        self._envelope = envelope
        self._size = sys.getsizeof(self._buffer)

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

    def as_pb_object(self) -> 'jina_pb2.Request':
        if self._deserialized is None:
            r = jina_pb2.Request()
            _buffer = self._buffer
            if self._envelope.compress == jina_pb2.Envelope.LZ4:
                import lz4.frame
                _buffer = lz4.frame.decompress(_buffer)
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
            _buffer = self._deserialized.SerializeToString()
            if self._envelope.compress == jina_pb2.Envelope.LZ4:
                import lz4.frame
                _buffer = lz4.frame.compress(_buffer)
            self._size = sys.getsizeof(_buffer)
            return _buffer
        else:
            # no touch, skip serialization, return original
            return self._buffer

    @property
    def size(self):
        """Get the size in bytes.

        To get the latest size, use it after :meth:`dump`
        """
        return self._size


class LazyMessage:

    def __init__(self, envelope: Union[bytes, 'jina_pb2.Envelope', None],
                 request: Union[bytes, 'jina_pb2.Request'], *args, **kwargs):
        self._size = 0
        if isinstance(envelope, bytes):
            self.envelope = jina_pb2.Envelope()
            self.envelope.ParseFromString(envelope)
            self._size = sys.getsizeof(envelope)
        elif isinstance(envelope, jina_pb2.Envelope):
            self.envelope = envelope
        else:
            # otherwise delay it to after request is built
            self.envelope = None

        if isinstance(request, bytes):
            self.request = LazyRequest(request, self.envelope)
            self._size += sys.getsizeof(request)
        elif isinstance(request, jina_pb2.Request):
            self.request = request  # type: Union['LazyRequest', 'jina_pb2.Request']
        else:
            raise TypeError(f'expecting request to be bytes or jina_pb2.Request, but receiving {type(request)}')

        if envelope is None:
            self.envelope = self._add_envelope(*args, **kwargs)
            # delayed assignment, now binding envelope to request
            if isinstance(self.request, LazyRequest):
                self.request._envelope = self.envelope

        if self.envelope.check_version:
            self._check_version()

    def as_pb_object(self) -> 'jina_pb2.Message':
        r = jina_pb2.Message()
        r.envelope.CopyFrom(self.envelope)
        if isinstance(self.request, jina_pb2.Request):
            req = self.request
        else:
            req = self.request.as_pb_object()
        r.request.CopyFrom(req)
        return r

    @property
    def is_data_request(self) -> bool:
        """check if the request is not a control request
        """
        return self.envelope.request_type != 'ControlRequest'

    def _add_envelope(self, pod_name, identity, num_part=1, check_version=False,
                      request_id: str = None, request_type: str = None) -> 'jina_pb2.Envelope':
        """Add envelope to a request and make it as a complete message, which can be transmitted between pods.

        .. note::
            this method should only be called at the gateway before the first pod of flow, not inside the flow.


        :param pod_name: the name of the current pod
        :param identity: the identity of the current pod
        :param num_part: the total parts of the message, 0 and 1 means single part
        :param check_version: turn on check_version 
        :return: the resulted protobuf message
        """
        envelope = jina_pb2.Envelope()
        envelope.receiver_id = identity
        if isinstance(self.request, jina_pb2.Request) or (request_id and request_type):
            # not lazy request, so we can directly access its request_id without worrying about
            # triggering the deserialization
            envelope.request_id = request_id or self.request.request_id
            envelope.request_type = request_type or \
                                    getattr(self.request, self.request.WhichOneof('body')).__class__.__name__
        elif isinstance(self.request, LazyRequest):
            raise TypeError('can add envelope to a LazyRequest object, '
                            'as it will trigger the deserialization.'
                            'in general, this invoke should not exist, '
                            'as add_envelope() is only called at the gateway')
        else:
            raise TypeError(f'expecting request in type: jina_pb2.Request, but receiving {type(self.request)}')

        envelope.timeout = 5000
        self._add_version(envelope)
        self._add_route(pod_name, identity, envelope)
        envelope.num_part.append(1)
        # keep in mind num_part works like FILO queue
        if num_part > 1:
            envelope.num_part.append(num_part)
        envelope.check_version = check_version
        return envelope

    def dump(self) -> List[bytes]:
        r0 = self.envelope.receiver_id.encode()
        r1 = self.envelope.SerializeToString()
        r2 = self.request.SerializeToString()
        m = [r0, r1, r2]
        self._size = sum(sys.getsizeof(r) for r in m)
        return m

    @property
    def colored_route(self) -> str:
        """ Get the string representation of the routes in a message.

        :return:
        """
        route_str = [r.pod for r in self.envelope.routes]
        route_str.append('⚐')
        from ..helper import colored
        return colored('▸', 'green').join(route_str)

    def add_route(self, name: str, identity: str):
        self._add_route(name, identity, self.envelope)

    def _add_route(self, name: str, identity: str, envelope: 'jina_pb2.Envelope') -> None:
        """Add a route to the envelope

        :param name: the name of the pod service
        :param identity: the identity of the pod service
        """
        r = envelope.routes.add()
        r.pod = name
        r.start_time.GetCurrentTime()
        r.pod_id = identity

    @property
    def size(self):
        """Get the size in bytes.

        To get the latest size, use it after :meth:`dump`
        """
        return self._size

    def _check_version(self):
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
                                        'incoming message has vcs_version %s, '
                                        'whereas local environment vcs_version is %s' % (
                                            self.envelope.version.vcs, os.environ.get('JINA_VCS_VERSION')))

        else:
            raise MismatchedVersion('version_check=True locally, '
                                    'but incoming message contains no version info in its envelope. '
                                    'the message is probably sent from a very outdated JINA version')

    def _add_version(self, envelope):
        envelope.version.jina = __version__
        envelope.version.proto = __proto_version__
        envelope.version.vcs = os.environ.get('JINA_VCS_VERSION', '')


class ControlMessage(LazyMessage):
    def __init__(self, command: 'jina_pb2.Request.ControlRequest',
                 *args, **kwargs):
        req = jina_pb2.Request()
        req.control.command = command
        super().__init__(None, req, *args, **kwargs)
