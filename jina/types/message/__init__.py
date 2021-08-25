import os
import sys
import traceback
from typing import Union, List, Optional

from ..request import Request
from ..request.control import ControlRequest
from ..request.data import DataRequest
from ... import __version__, __proto_version__
from ...enums import CompressAlgo
from ...excepts import MismatchedVersion
from ...helper import colored
from ...logging.predefined import default_logger
from ...proto import jina_pb2
from ...types.routing.table import RoutingTable

if False:
    from ...executors import BaseExecutor

__all__ = ['Message']


class Message:
    """
    :class:`Message` is one of the **primitive data type** in Jina.

    It offers a Pythonic interface to allow users access and manipulate
    :class:`jina.jina_pb2.MessageProto` object without working with Protobuf itself.

    A container class for :class:`jina_pb2.MessageProto`. Note, the Protobuf version of :class:`jina_pb2.MessageProto`
    contains a :class:`jina_pb2.EnvelopeProto` and :class:`jina_pb2.RequestProto`. Here, it contains:
        - a :class:`jina_pb2.EnvelopeProto` object
        - and one of:
            - a :class:`Request` object wrapping :class:`jina_pb2.RequestProto`
            - a :class:`jina_pb2.RequestProto` object

    It provide a generic view of as :class:`jina_pb2.MessageProto`, allowing one to access its member, request
    and envelope as if using :class:`jina_pb2.MessageProto` object directly.

    This class also collected all helper functions related to :class:`jina_pb2.MessageProto` into one place.

    :param envelope: Represents a Envelope, a part of the Message.
    :param request: Represents a Request
    :param args: Additional positional arguments.
    :param kwargs: Additional keyword arguments.
    """

    def __init__(
        self,
        envelope: Optional[Union[bytes, 'jina_pb2.EnvelopeProto']],
        request: Union[bytes, 'jina_pb2.RequestProto'],
        *args,
        **kwargs,
    ):
        self._size = 0
        if isinstance(envelope, bytes):
            self.envelope = jina_pb2.EnvelopeProto()
            self.envelope.ParseFromString(envelope)
            self._size = sys.getsizeof(envelope)
        elif isinstance(envelope, jina_pb2.EnvelopeProto):
            self.envelope = envelope
        else:
            # otherwise delay it to after request is built
            self.envelope = None

        self.request = request
        if envelope is None:
            self.envelope = self._add_envelope(*args, **kwargs)
            # delayed assignment, now binding envelope to request
            if isinstance(self.request, Request):
                self.request._envelope = self.envelope

            self.envelope.header.CopyFrom(self.request.header)

        if self.envelope.check_version:
            self._check_version()

    @classmethod
    def from_proto(cls, msg: 'jina_pb2.MessageProto'):
        """Creates a new Message object from a given :class:`MessageProto` object.

        :param msg: the to-be-copied message
        :return: the new message object
        """
        return cls(msg.envelope, msg.request)

    @property
    def request(self) -> 'Request':
        """
        Get the request.

        :return: request
        """
        if (
            self.envelope
            and isinstance(self._request, Request)
            and not isinstance(self._request, DataRequest)
            and not isinstance(self._request, ControlRequest)
        ):
            self._request = self._request.as_typed_request(self.envelope.request_type)
        return self._request

    @request.setter
    def request(self, val: Union[bytes, 'jina_pb2.RequestProto']):
        """
        Set the request to :param: `val`.

        :param val: serialized Request
        """
        if isinstance(val, bytes):
            self._request = Request(
                val,
                CompressAlgo.from_string(self.envelope.compression.algorithm)
                if self.envelope
                else None,
            )
            self._size += sys.getsizeof(val)
        elif isinstance(val, Request):
            self._request = val
        elif isinstance(val, jina_pb2.RequestProto):
            self._request = Request(
                val,
                CompressAlgo.from_string(self.envelope.compression.algorithm)
                if self.envelope
                else None,
            )
        else:
            raise TypeError(
                f'expecting request to be bytes or jina_pb2.RequestProto, but receiving {type(val)}'
            )

    @property
    def proto(self) -> 'jina_pb2.MessageProto':
        """
        Get the RequestProto.

        :return: protobuf object
        """
        r = jina_pb2.MessageProto()
        r.envelope.CopyFrom(self.envelope)
        if isinstance(self.request, jina_pb2.RequestProto):
            req = self.request
        else:
            req = self.request.proto
        r.request.CopyFrom(req)
        return r

    @property
    def is_data_request(self) -> bool:
        """check if the request is not a control request

        .. warning::
            If ``request`` change the type, e.g. by leveraging the feature of ``oneof``, this
            property wont be updated. This is not considered as a good practice.

        :return: boolean which states if data is requested
        """
        return self.envelope.request_type == 'DataRequest'

    def _add_envelope(
        self,
        pod_name,
        identity,
        check_version=False,
        request_id: Optional[str] = None,
        request_type: Optional[str] = None,
        compress: str = 'NONE',
        compress_min_bytes: int = 0,
        compress_min_ratio: float = 1.0,
        routing_table: Optional[str] = None,
        send_routing_table: bool = True,
        *args,
        **kwargs,
    ) -> 'jina_pb2.EnvelopeProto':
        """Add envelope to a request and make it as a complete message, which can be transmitted between pods.

        .. note::
            this method should only be called at the gateway before the first pod of flow, not inside the flow.


        :param pod_name: the name of the current pod
        :param identity: the identity of the current pod
        :param check_version: turn on check_version
        :param args: Additional positional arguments
        :param kwargs: Additional keyword arguments
        :param request_id: request id of the envelope
        :param request_type: request type of the envelope
        :param compress: used compression algorithm
        :param compress_min_bytes: used for configuring compression
        :param compress_min_ratio: used for configuring compression
        :param routing_table: routing graph filled by gateway
        :param send_routing_table: include the routing table in the envelope
        :return: the resulted protobuf message
        """
        envelope = jina_pb2.EnvelopeProto()
        envelope.receiver_id = identity
        if isinstance(self.request, jina_pb2.RequestProto) or (
            request_id and request_type
        ):
            # not lazy request, so we can directly access its request_id without worrying about
            # triggering the deserialization
            envelope.request_id = request_id or self.request.request_id
            envelope.request_type = (
                request_type
                or getattr(
                    self.request, self.request.WhichOneof('body')
                ).__class__.__name__
            )

            # for compatibility
            if envelope.request_type.endswith('Proto'):
                envelope.request_type = envelope.request_type.replace('Proto', '')

        elif isinstance(self.request, Request):
            envelope.request_id = request_id or self.request.request_id
            envelope.request_type = request_type or self.request.request_type
            # for compatibility
            if envelope.request_type.endswith('Proto'):
                envelope.request_type = envelope.request_type.replace('Proto', '')

            # raise TypeError('can not add envelope to a Request object, '
            #                 'as it will trigger the deserialization.'
            #                 'in general, this invoke should not exist, '
            #                 'as add_envelope() is only called at the gateway')
        else:
            raise TypeError(
                f'expecting request in type: jina_pb2.RequestProto, but receiving {type(self.request)}'
            )

        envelope.compression.algorithm = str(compress)
        envelope.compression.min_ratio = compress_min_ratio
        envelope.compression.min_bytes = compress_min_bytes
        envelope.timeout = 5000
        if routing_table is not None and send_routing_table:
            envelope.routing_table.CopyFrom(RoutingTable(routing_table).proto)
        self._add_version(envelope)
        self._add_route(pod_name, identity, envelope)
        envelope.check_version = check_version
        return envelope

    def dump(self) -> List[bytes]:
        """
        Get the message in a list of bytes.

        :return: array, containing encoded receiver id, serialized envelope and the compressed serialized envelope
        """
        r2 = self.request.SerializeToString()
        r2 = self._compress(r2)

        r0 = self.envelope.receiver_id.encode()
        r1 = self.envelope.SerializePartialToString()
        m = [r0, r1, r2]
        self._size = sum(sys.getsizeof(r) for r in m)
        return m

    def _compress(self, data: bytes) -> bytes:
        # no further compression or post processing is required
        if isinstance(self.request, Request) and not self.request.is_decompressed:
            return data

        # otherwise there are two cases
        # 1. it is a lazy request, and being used, so `self.request.SerializeToString()` is a new uncompressed string
        # 2. it is a regular request, `self.request.SerializeToString()` is a uncompressed string
        # either way need compress
        if not self.envelope.compression.algorithm:
            return data

        ctag = CompressAlgo.from_string(self.envelope.compression.algorithm)

        if ctag == CompressAlgo.NONE:
            return data

        _size_before = sys.getsizeof(data)

        # lower than hwm, pass compression
        if (
            _size_before < self.envelope.compression.min_bytes
            or self.envelope.compression.min_bytes < 0
        ):
            self.envelope.compression.algorithm = 'NONE'
            return data

        try:
            if ctag == CompressAlgo.LZ4:
                import lz4.frame

                c_data = lz4.frame.compress(data)
            elif ctag == CompressAlgo.BZ2:
                import bz2

                c_data = bz2.compress(data)
            elif ctag == CompressAlgo.LZMA:
                import lzma

                c_data = lzma.compress(data)
            elif ctag == CompressAlgo.ZLIB:
                import zlib

                c_data = zlib.compress(data)
            elif ctag == CompressAlgo.GZIP:
                import gzip

                c_data = gzip.compress(data)

            _size_after = sys.getsizeof(c_data)
            _c_ratio = _size_before / _size_after

            if _c_ratio > self.envelope.compression.min_ratio:
                data = c_data
            else:
                # compression rate is too bad, dont bother
                # save time on decompression
                default_logger.debug(
                    f'compression rate {(_size_before / _size_after):.2f}% '
                    f'is lower than min_ratio '
                    f'{self.envelope.compression.min_ratio}'
                )
                self.envelope.compression.algorithm = 'NONE'
        except Exception as ex:
            default_logger.debug(
                f'compression={str(ctag)} failed, fallback to compression="NONE". reason: {ex!r}'
            )
            self.envelope.compression.algorithm = 'NONE'

        return data

    @property
    def colored_route(self) -> str:
        """Get the string representation of the routes in a message.

        :return: colored route
        """

        def _pod_str(r):
            result = r.pod
            if r.status.code == jina_pb2.StatusProto.ERROR:
                result += '✖'
                result = colored(result, 'red')
            elif r.status.code == jina_pb2.StatusProto.ERROR_CHAINED:
                result += '∅'
                result = colored(result, 'yellow')
            return result

        route_str = [_pod_str(r) for r in self.envelope.routes]
        route_str.append('⚐')
        return colored('▸', 'green').join(route_str)

    def add_route(self, name: str, identity: str):
        """Add a route to the envelope.

        :param name: the name of the pod service
        :param identity: the identity of the pod service
        """
        self._add_route(name, identity, self.envelope)

    def _add_route(
        self, name: str, identity: str, envelope: 'jina_pb2.EnvelopeProto'
    ) -> None:
        """Add a route to the envelope.

        :param name: the name of the pod service
        :param identity: the identity of the pod service
        :param envelope: protobuf definition of the envelope
        """
        r = envelope.routes.add()
        r.pod = name
        r.start_time.GetCurrentTime()
        r.pod_id = identity

    @property
    def size(self):
        """Get the size in bytes.

        To get the latest size, use it after :meth:`dump`
        :return: size of the message
        """
        return self._size

    def _check_version(self):
        if hasattr(self.envelope, 'version'):
            if not self.envelope.version.jina:
                # only happen in unittest
                default_logger.warning(
                    'incoming message contains empty "version.jina", '
                    'you may ignore it in debug/unittest mode. '
                    'otherwise please check if gateway service set correct version'
                )
            elif __version__ != self.envelope.version.jina:
                raise MismatchedVersion(
                    'mismatched JINA version! '
                    f'incoming message has JINA version {self.envelope.version.jina}, '
                    f'whereas local JINA version {__version__}'
                )

            if not self.envelope.version.proto:
                # only happen in unittest
                default_logger.warning(
                    'incoming message contains empty "version.proto", '
                    'you may ignore it in debug/unittest mode. '
                    'otherwise please check if gateway service set correct version'
                )
            elif __proto_version__ != self.envelope.version.proto:
                raise MismatchedVersion(
                    'mismatched protobuf version! '
                    f'incoming message has protobuf version {self.envelope.version.proto}, '
                    f'whereas local protobuf version {__proto_version__}'
                )

            if not self.envelope.version.vcs or not os.environ.get('JINA_VCS_VERSION'):
                default_logger.warning(
                    'incoming message contains empty "version.vcs", '
                    'you may ignore it in debug/unittest mode, '
                    'or if you run jina OUTSIDE docker container where JINA_VCS_VERSION is unset'
                    'otherwise please check if gateway service set correct version'
                )
            elif os.environ.get('JINA_VCS_VERSION') != self.envelope.version.vcs:
                raise MismatchedVersion(
                    'mismatched vcs version! '
                    f'incoming message has vcs_version {self.envelope.version.vcs}, '
                    f'whereas local environment vcs_version is '
                    f'{os.environ.get("JINA_VCS_VERSION")}'
                )

        else:
            raise MismatchedVersion(
                'version_check=True locally, '
                'but incoming message contains no version info in its envelope. '
                'the message is probably sent from a very outdated JINA version'
            )

    def _add_version(self, envelope):
        envelope.version.jina = __version__
        envelope.version.proto = __proto_version__
        envelope.version.vcs = os.environ.get('JINA_VCS_VERSION', '')

    def update_timestamp(self):
        """Update the timestamp of the last route"""
        self.envelope.routes[-1].end_time.GetCurrentTime()

    @property
    def response(self) -> 'Request':
        """Get the response of the message in protobuf.

        .. note::
            This should be only called at Gateway
        :return: request object which contains the response
        """
        self.envelope.routes[0].end_time.GetCurrentTime()
        self.request.status.CopyFrom(self.envelope.status)
        self.request.routes.extend(self.envelope.routes)
        return self.request

    def merge_envelope_from(self, msgs: List['Message']):
        """
        Extend the current envelope routes with :param: `msgs`.

        :param msgs: List of msgs.
        """
        routes = {(r.pod + r.pod_id): r for m in msgs for r in m.envelope.routes}
        self.envelope.ClearField('routes')
        self.envelope.routes.extend(
            sorted(
                routes.values(),
                key=lambda x: (x.start_time.seconds, x.start_time.nanos),
            )
        )

    def add_exception(
        self, ex: Optional['Exception'] = None, executor: 'BaseExecutor' = None
    ) -> None:
        """Add exception to the last route in the envelope

        :param ex: Exception to be added
        :param executor: Executor related to the exception
        """
        d = self.envelope.routes[-1].status
        if ex:
            self.envelope.status.code = jina_pb2.StatusProto.ERROR
            if not self.envelope.status.description:
                self.envelope.status.description = repr(ex)
            d.code = jina_pb2.StatusProto.ERROR
            d.description = repr(ex)
            d.exception.executor = executor.__class__.__name__
            d.exception.name = ex.__class__.__name__
            d.exception.args.extend([str(v) for v in ex.args])
            d.exception.stacks.extend(
                traceback.format_exception(
                    etype=type(ex), value=ex, tb=ex.__traceback__
                )
            )
        else:
            d.code = jina_pb2.StatusProto.ERROR_CHAINED

    @property
    def is_error(self) -> bool:
        """
        Return if the envelope status is ERROR.

         :return: boolean stating if the status code of the envelope is error
        """
        return self.envelope.status.code >= jina_pb2.StatusProto.ERROR

    @property
    def is_ready(self) -> bool:
        """
        Return if the envelope status is READY.

        :return: boolean stating if the status code of the envelope is ready
        """
        return self.envelope.status.code == jina_pb2.StatusProto.READY
