__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import os
import sys
import tempfile
from typing import List, Callable
from typing import Tuple

import tornado.ioloop
import zmq
import zmq.asyncio
from zmq.eventloop.zmqstream import ZMQStream

from .zmq import Zmqlet
from .. import __default_host__
from ..enums import SocketType
from ..excepts import MismatchedVersion
from ..helper import get_random_identity, use_uvloop
from ..logging import default_logger
from ..proto import jina_pb2

if False:
    # fix type-hint complain for sphinx and flake
    pass


class ZmqStreamlet(Zmqlet):
    """A `Zmqlet` object can send/receive data to/from ZeroMQ socket and invoke callback function. It
    has three sockets for input, output and control. `Zmqlet` is one of the key components in :class:`jina.peapods.pea.BasePea`.
    """

    def register_pollin(self):
        use_uvloop()
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())

        self.io_loop = tornado.ioloop.IOLoop.current()
        self.in_sock = ZMQStream(self.in_sock, self.io_loop)
        self.out_sock = ZMQStream(self.out_sock, self.io_loop)
        self.ctrl_sock = ZMQStream(self.ctrl_sock, self.io_loop)
        self.in_sock.stop_on_recv()

    def close(self):
        """Close all sockets and shutdown the ZMQ context associated to this `Zmqlet`. """
        if not self.is_closed:
            super().close()
            self.io_loop.stop()

    def pause_pollin(self):
        """Remove :attr:`in_sock` from the poller """
        self.in_sock.stop_on_recv()

    def resume_pollin(self):
        """Put :attr:`in_sock` back to the poller """
        self.in_sock.on_recv(self._in_sock_callback)

    def start(self, callback: Callable[['jina_pb2.Message'], None]):
        def _callback(msg, sock_type):
            msg, num_bytes = _prepare_recv_msg(sock_type, msg, **self.send_recv_kwargs)
            self.bytes_recv += num_bytes
            self.msg_recv += 1

            msg = callback(msg)

            if msg:
                self.send_message(msg)

        self._in_sock_callback = lambda x: _callback(x, self.in_sock_type)
        self.in_sock.on_recv(self._in_sock_callback)
        self.ctrl_sock.on_recv(lambda x: _callback(x, self.ctrl_sock_type))
        if self.out_sock_type == zmq.ROUTER:
            self.out_sock.on_recv(lambda x: _callback(x, self.out_sock_type))
        self.io_loop.start()
        self.io_loop.clear_current()
        self.io_loop.close(all_fds=True)


def send_ctrl_message(address: str, cmd: 'jina_pb2.Request.ControlRequest', timeout: int):
    """Send a control message to a specific address and wait for the response

    :param address: the socket address to send
    :param cmd: the control command to send
    :param timeout: the waiting time (in ms) for the response
    """
    # control message is short, set a timeout and ask for quick response
    with zmq.Context() as ctx:
        ctx.setsockopt(zmq.LINGER, 0)
        sock, _ = _init_socket(ctx, address, None, SocketType.PAIR_CONNECT)
        req = jina_pb2.Request()
        req.control.command = cmd
        msg = add_envelope(req, 'ctl', '')
        send_message(sock, msg, timeout)
        r = None
        try:
            r, _ = recv_message(sock, timeout)
        except TimeoutError:
            pass
        finally:
            sock.close()
        return r


def send_message(sock: 'ZMQStream', msg: 'jina_pb2.Message', timeout: int = -1,
                 array_in_pb: bool = False, compress_hwm: int = -1, compress_lwm: float = 1., **kwargs) -> int:
    """Send a protobuf message to a socket

    :param sock: the target socket to send
    :param msg: the protobuf message
    :param timeout: waiting time (in seconds) for sending
    :param array_in_pb: send the numpy array within the protobuf message, this often yields worse network efficiency
    :param compress_hwm: message bigger than this size (in bytes) will be compressed by lz4 algorithm, set to -1 to disable this feature.
    :param compress_lwm: the low watermark that enables the sending of a compressed message.
    :return: the size (in bytes) of the sent message
    """
    num_bytes = 0
    try:
        _msg, num_bytes = _prep_send_msg(array_in_pb, compress_hwm, compress_lwm, msg, sock, timeout)

        sock.send_multipart(_msg)
    except zmq.error.Again:
        raise TimeoutError(
            'cannot send message to sock %s after timeout=%dms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? ' % (
                sock, timeout))
    except zmq.error.ZMQError as ex:
        default_logger.critical(ex)
    except Exception as ex:
        raise ex

    return num_bytes


def _prep_send_msg(array_in_pb, compress_hwm, compress_lwm, msg, sock, timeout):
    if timeout > 0:
        sock.setsockopt(zmq.SNDTIMEO, timeout)
    else:
        sock.setsockopt(zmq.SNDTIMEO, -1)
    c_id = msg.envelope.receiver_id
    if array_in_pb:
        _msg, num_bytes = _prepare_send_msg(c_id, [msg.SerializeToString()], compress_hwm, compress_lwm)
    else:
        doc_bytes, chunk_bytes, chunk_byte_type = _extract_bytes_from_msg(msg)
        # now buffer are removed from message, hoping for faster de/serialization
        _msg = [msg.SerializeToString(),  # 1
                chunk_byte_type,  # 2
                b'%d' % len(doc_bytes), b'%d' % len(chunk_bytes),  # 3, 4
                *doc_bytes, *chunk_bytes]

        _msg, num_bytes = _prepare_send_msg(c_id, _msg, compress_hwm, compress_lwm)
    return _msg, num_bytes


def recv_message(sock: 'zmq.Socket', timeout: int = -1, check_version: bool = False, **kwargs) -> Tuple[
    'jina_pb2.Message', int]:
    """ Receive a protobuf message from a socket

    :param sock: the socket to pull from
    :param timeout: max wait time for pulling, -1 means wait forever
    :param check_version: check if the jina, protobuf version info in the incoming message consists with the local versions
    :return: a tuple of two pieces

            - the received protobuf message
            - the size of the message in bytes
    """
    try:
        if timeout > 0:
            sock.setsockopt(zmq.RCVTIMEO, timeout)
        else:
            sock.setsockopt(zmq.RCVTIMEO, -1)

        msg_data = sock.recv_multipart()

        return _prepare_recv_msg(sock, msg_data, check_version)

    except zmq.error.Again:
        raise TimeoutError(
            'no response from sock %s after timeout=%dms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? ' % (
                sock, timeout))
    except Exception as ex:
        raise ex
    finally:
        sock.setsockopt(zmq.RCVTIMEO, -1)


def _prepare_send_msg(client_id, bodies: List[bytes], compress_hwm: int, compress_lwm: float):
    if isinstance(client_id, str):
        client_id = client_id.encode()

    _size_before = sum(sys.getsizeof(m) for m in bodies)
    if _size_before > compress_hwm > 0:
        from ..logging import default_logger
        import lz4.frame
        _bodies = [lz4.frame.compress(m) for m in bodies]
        is_compressed = b'1'
        _size_after = sum(sys.getsizeof(m) for m in _bodies)
        rate = _size_after / _size_before
        default_logger.debug(f'compressed, before: {_size_before} after: {_size_after}, '
                             f'ratio: {(_size_after / _size_before * 100):.0f}%')
        if rate > compress_lwm:
            _bodies = bodies
            is_compressed = b'0'
            default_logger.debug(f'ineffective compression as the rate {rate:.2f} is higher than {compress_lwm}')
    else:
        _bodies = bodies
        is_compressed = b'0'

    _header = [client_id, is_compressed]
    msg = _header + _bodies
    num_bytes = sum(sys.getsizeof(m) for m in msg)
    return msg, num_bytes


def _prepare_recv_msg(msg_data, check_version: bool, **kwargs):
    # if sock.type == zmq.DEALER:
    #     # dealer consumes the first part of the message as id, we need to prepend it back
    #     msg_data = [' '] + msg_data
    # elif sock.type == zmq.ROUTER:
    #     # the router appends dealer id when receive it, we need to remove it
    #     msg_data.pop(0)

    if msg_data[1] == b'1':
        # body message is compressed
        import lz4.frame
        for l in range(2, len(msg_data)):
            msg_data[l] = lz4.frame.decompress(msg_data[l])

    msg = jina_pb2.Message()

    num_bytes = sum(sys.getsizeof(m) for m in msg_data)

    msg.ParseFromString(msg_data[2])

    if check_version:
        _check_msg_version(msg)

    # now we have a barebone msg, we need to fill in data
    if len(msg_data) > 3:
        _fill_buffer_to_msg(msg, msg_data, offset=3)

    return msg, num_bytes


def _get_random_ipc() -> str:
    """Get a random IPC address for control port """
    try:
        tmp = os.environ['JINA_IPC_SOCK_TMP']
        if not os.path.exists(tmp):
            raise ValueError(f'This directory for sockets ({tmp}) does not seems to exist.')
        tmp = os.path.join(tmp, get_random_identity())
    except KeyError:
        tmp = tempfile.NamedTemporaryFile().name
    return f'ipc://{tmp}'


def _init_socket(ctx: 'zmq.Context', host: str, port: int,
                 socket_type: 'SocketType', identity: 'str' = None, use_ipc: bool = False) -> Tuple['zmq.Socket', str]:
    sock = {
        SocketType.PULL_BIND: lambda: ctx.socket(zmq.PULL),
        SocketType.PULL_CONNECT: lambda: ctx.socket(zmq.PULL),
        SocketType.SUB_BIND: lambda: ctx.socket(zmq.SUB),
        SocketType.SUB_CONNECT: lambda: ctx.socket(zmq.SUB),
        SocketType.PUB_BIND: lambda: ctx.socket(zmq.PUB),
        SocketType.PUB_CONNECT: lambda: ctx.socket(zmq.PUB),
        SocketType.PUSH_BIND: lambda: ctx.socket(zmq.PUSH),
        SocketType.PUSH_CONNECT: lambda: ctx.socket(zmq.PUSH),
        SocketType.PAIR_BIND: lambda: ctx.socket(zmq.PAIR),
        SocketType.PAIR_CONNECT: lambda: ctx.socket(zmq.PAIR),
        SocketType.ROUTER_BIND: lambda: ctx.socket(zmq.ROUTER),
        SocketType.DEALER_CONNECT: lambda: ctx.socket(zmq.DEALER),
    }[socket_type]()
    sock.setsockopt(zmq.LINGER, 0)

    if socket_type == SocketType.DEALER_CONNECT:
        sock.set_string(zmq.IDENTITY, identity)

    # if not socket_type.is_pubsub:
    #     sock.hwm = int(os.environ.get('JINA_SOCKET_HWM', 1))

    if socket_type.is_bind:
        if use_ipc:
            sock.bind(host)
        else:
            # JEP2, if it is bind, then always bind to local
            if host != __default_host__:
                default_logger.warning(
                    f'host is set from {host} to {__default_host__} as the socket is in BIND type')
                host = __default_host__
            if port is None:
                sock.bind_to_random_port(f'tcp://{host}')
            else:
                try:
                    sock.bind('tcp://%s:%d' % (host, port))
                except zmq.error.ZMQError as ex:
                    default_logger.error('error when binding port %d to %s' % (port, host))
                    raise ex
    else:
        if port is None:
            sock.connect(host)
        else:
            sock.connect('tcp://%s:%d' % (host, port))

    if socket_type in {SocketType.SUB_CONNECT, SocketType.SUB_BIND}:
        # sock.setsockopt(zmq.SUBSCRIBE, identity.encode('ascii') if identity else b'')
        sock.subscribe('')  # An empty shall subscribe to all incoming messages

    return sock, sock.getsockopt_string(zmq.LAST_ENDPOINT)


def _check_msg_version(msg: 'jina_pb2.Message'):
    from ..logging import default_logger
    from .. import __version__, __proto_version__
    if hasattr(msg.envelope, 'version'):
        if not msg.envelope.version.jina:
            # only happen in unittest
            default_logger.warning('incoming message contains empty "version.jina", '
                                   'you may ignore it in debug/unittest mode. '
                                   'otherwise please check if gateway service set correct version')
        elif __version__ != msg.envelope.version.jina:
            raise MismatchedVersion('mismatched JINA version! '
                                    'incoming message has JINA version %s, whereas local JINA version %s' % (
                                        msg.envelope.version.jina, __version__))

        if not msg.envelope.version.proto:
            # only happen in unittest
            default_logger.warning('incoming message contains empty "version.proto", '
                                   'you may ignore it in debug/unittest mode. '
                                   'otherwise please check if gateway service set correct version')
        elif __proto_version__ != msg.envelope.version.proto:
            raise MismatchedVersion('mismatched protobuf version! '
                                    'incoming message has protobuf version %s, whereas local protobuf version %s' % (
                                        msg.envelope.version.proto, __proto_version__))

        if not msg.envelope.version.vcs or not os.environ.get('JINA_VCS_VERSION'):
            default_logger.warning('incoming message contains empty "version.vcs", '
                                   'you may ignore it in debug/unittest mode, '
                                   'or if you run jina OUTSIDE docker container where JINA_VCS_VERSION is unset'
                                   'otherwise please check if gateway service set correct version')
        elif os.environ.get('JINA_VCS_VERSION') != msg.envelope.version.vcs:
            raise MismatchedVersion('mismatched vcs version! '
                                    'incoming message has vcs_version %s, whereas local environment vcs_version is %s' % (
                                        msg.envelope.version.vcs, os.environ.get('JINA_VCS_VERSION')))

    else:
        raise MismatchedVersion('version_check=True locally, '
                                'but incoming message contains no version info in its envelope. '
                                'the message is probably sent from a very outdated JINA version')


def _extract_bytes_from_msg(msg: 'jina_pb2.Message') -> Tuple:
    doc_bytes = []
    chunk_bytes = []
    chunk_byte_type = b''

    docs = msg.request.train.docs or msg.request.index.docs or msg.request.search.docs
    # for train request
    for d in docs:
        doc_bytes.append(d.buffer)
        d.ClearField('buffer')

        for c in d.chunks:
            # oneof content {
            # string text = 2;
            # NdArray blob = 3;
            # bytes raw = 7;
            # }
            chunk_bytes.append(c.embedding.buffer)
            c.embedding.ClearField('buffer')

            ctype = c.WhichOneof('content') or ''
            chunk_byte_type = ctype.encode()
            if ctype == 'buffer':
                chunk_bytes.append(c.buffer)
                c.ClearField('buffer')
            elif ctype == 'blob':
                chunk_bytes.append(c.blob.buffer)
                c.blob.ClearField('buffer')
            elif ctype == 'text':
                chunk_bytes.append(c.text.encode())
                c.ClearField('text')

    return doc_bytes, chunk_bytes, chunk_byte_type


def _fill_buffer_to_msg(msg: 'jina_pb2.Message', msg_data: List[bytes], offset: int = 2):
    chunk_byte_type = msg_data[offset].decode()
    doc_bytes_len = int(msg_data[offset + 1])
    chunk_bytes_len = int(msg_data[offset + 2])
    doc_bytes = msg_data[(offset + 3):(offset + 3 + doc_bytes_len)]
    chunk_bytes = msg_data[(offset + 3 + doc_bytes_len):]
    c_idx = 0
    d_idx = 0

    if len(chunk_bytes) != chunk_bytes_len:
        raise ValueError('"chunk_bytes_len"=%d in message, but the actual length is %d' % (
            chunk_bytes_len, len(chunk_bytes)))

    docs = msg.request.train.docs or msg.request.index.docs or msg.request.search.docs
    for d in docs:
        if doc_bytes and doc_bytes[d_idx]:
            d.buffer = doc_bytes[d_idx]
            d_idx += 1

        for c in d.chunks:
            if chunk_bytes and chunk_bytes[c_idx]:
                c.embedding.buffer = chunk_bytes[c_idx]
            c_idx += 1

            if chunk_byte_type == 'buffer':
                c.buffer = chunk_bytes[c_idx]
                c_idx += 1
            elif chunk_byte_type == 'blob':
                c.blob.buffer = chunk_bytes[c_idx]
                c_idx += 1
            elif chunk_byte_type == 'text':
                c.text = chunk_bytes[c_idx].decode()
                c_idx += 1


def remove_envelope(m: 'jina_pb2.Message') -> 'jina_pb2.Request':
    """Remove the envelope and return only the request body """

    # body.request_id = m.envelope.request_id
    m.envelope.routes[0].end_time.GetCurrentTime()
    # if self.args.route_table:
    #     self.logger.info('route: %s' % router2str(m))
    #     self.logger.info('route table: \n%s' % make_route_table(m.envelope.routes, include_gateway=True))
    # if self.args.dump_route:
    #     self.args.dump_route.write(MessageToJson(m.envelope, indent=0).replace('\n', '') + '\n')
    #     self.args.dump_route.flush()
    return m.request


def _add_route(evlp, pod_name, identity):
    r = evlp.routes.add()
    r.pod = pod_name
    r.start_time.GetCurrentTime()
    r.pod_id = identity


def add_envelope(req, pod_name, identity, num_part=1) -> 'jina_pb2.Message':
    """Add envelope to a request and make it as a complete message, which can be transmitted between pods.

    :param req: the protobuf request
    :param pod_name: the name of the current pod
    :param identity: the identity of the current pod
    :param num_part: the total parts of the message, 0 and 1 means single part
    :return: the resulted protobuf message
    """
    msg = jina_pb2.Message()
    msg.envelope.receiver_id = identity
    if req.request_id is not None:
        msg.envelope.request_id = req.request_id
    else:
        raise AttributeError('"request_id" is missing or unset!')
    msg.envelope.timeout = 5000
    _add_version(msg.envelope)
    _add_route(msg.envelope, pod_name, identity)
    msg.request.CopyFrom(req)
    msg.envelope.num_part.append(1)
    if num_part > 1:
        msg.envelope.num_part.append(num_part)
    return msg


def _add_version(evlp: 'jina_pb2.Envelope'):
    from .. import __version__, __proto_version__
    evlp.version.jina = __version__
    evlp.version.proto = __proto_version__
    evlp.version.vcs = os.environ.get('JINA_VCS_VERSION', '')
