__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import asyncio
import os
import sys
import tempfile
import time
from typing import List, Callable, Optional
from typing import Tuple

import zmq
import zmq.asyncio

from .. import __default_host__
from ..enums import SocketType
from ..excepts import MismatchedVersion
from ..helper import colored, get_random_identity, get_readable_size
from ..logging import default_logger, profile_logger
from ..logging.base import get_logger
from ..proto import jina_pb2, is_data_request

if False:
    # fix type-hint complain for sphinx and flake
    import argparse
    import logging


class Zmqlet:
    """A `Zmqlet` object can send/receive data to/from ZeroMQ socket and invoke callback function. It
    has three sockets for input, output and control. `Zmqlet` is one of the key components in :class:`jina.peapods.pea.BasePea`.
    """

    def __init__(self, args: 'argparse.Namespace', logger: 'logging.Logger' = None):
        """

        :param args: the parsed arguments from the CLI
        :param logger: the logger to use
        """
        self.args = args
        self.name = args.name or self.__class__.__name__
        self.logger = logger or get_logger(self.name, **vars(args))
        if args.compress_hwm > 0:
            try:
                import lz4
                self.logger.success(f'compression is enabled and the high watermark is {args.compress_hwm} bytes')
            except ModuleNotFoundError:
                self.logger.error(f'compression is enabled but you do not have lz4 package. '
                                  f'use pip install "jina[lz4]" to install this dependency')
                args.compress_hwm = -1  # disable the compression
        self.send_recv_kwargs = vars(args)
        self.ctrl_addr, self.ctrl_with_ipc = self.get_ctrl_address(args)
        self.opened_socks = []
        self.bytes_sent = 0
        self.bytes_recv = 0
        self.msg_recv = 0
        self.msg_sent = 0
        self.ctx, self.in_sock, self.out_sock, self.ctrl_sock = self.init_sockets()
        self.poller = zmq.Poller()
        self.poller.register(self.in_sock, zmq.POLLIN)
        self.poller.register(self.ctrl_sock, zmq.POLLIN)
        if self.out_sock.type == zmq.ROUTER:
            self.poller.register(self.out_sock, zmq.POLLIN)
        if self.in_sock.type == zmq.DEALER:
            self.send_idle()

    def pause_pollin(self):
        """Remove :attr:`in_sock` from the poller """
        self.poller.unregister(self.in_sock)

    def resume_pollin(self):
        """Put :attr:`in_sock` back to the poller """
        self.poller.register(self.in_sock)

    @staticmethod
    def get_ctrl_address(args: 'argparse.Namespace') -> Tuple[str, bool]:
        """Get the address of the control socket

        :param args: the parsed arguments from the CLI
        :return: A tuple of two pieces:

            - a string of control address
            - a bool of whether using IPC protocol for controlling

        """
        ctrl_with_ipc = (os.name != 'nt') and args.ctrl_with_ipc
        if ctrl_with_ipc:
            return _get_random_ipc(), ctrl_with_ipc
        else:
            return 'tcp://%s:%d' % (args.host, args.port_ctrl), ctrl_with_ipc

    def _pull(self, interval: int = 1):
        socks = dict(self.poller.poll(interval))
        # the priority ctrl_sock > in_sock
        if socks.get(self.ctrl_sock) == zmq.POLLIN:
            return self.ctrl_sock
        elif socks.get(self.out_sock) == zmq.POLLIN:
            return self.out_sock  # for dealer return idle status to router
        elif socks.get(self.in_sock) == zmq.POLLIN:
            return self.in_sock

    def close_sockets(self):
        """Close input, output and control sockets of this `Zmqlet`. """
        for k in self.opened_socks:
            k.close()

    def init_sockets(self) -> Tuple:
        """Initialize all sockets and the ZMQ context.

        :return: A tuple of four pieces:

            - ZMQ context
            - the input socket
            - the output socket
            - the control socket
        """
        ctx = self._get_zmq_ctx()
        ctx.setsockopt(zmq.LINGER, 0)

        self.logger.info('setting up sockets...')
        try:
            if self.ctrl_with_ipc:
                ctrl_sock, ctrl_addr = _init_socket(ctx, self.ctrl_addr, None, SocketType.PAIR_BIND,
                                                    use_ipc=self.ctrl_with_ipc)
            else:
                ctrl_sock, ctrl_addr = _init_socket(ctx, __default_host__, self.args.port_ctrl, SocketType.PAIR_BIND)
            self.logger.debug('control over %s' % (colored(ctrl_addr, 'yellow')))
            self.opened_socks.append(ctrl_sock)

            in_sock, in_addr = _init_socket(ctx, self.args.host_in, self.args.port_in, self.args.socket_in,
                                            self.args.identity)
            self.logger.debug('input %s:%s' % (self.args.host_in, colored(self.args.port_in, 'yellow')))
            self.opened_socks.append(in_sock)

            out_sock, out_addr = _init_socket(ctx, self.args.host_out, self.args.port_out, self.args.socket_out,
                                              self.args.identity)
            self.logger.debug('output %s:%s' % (self.args.host_out, colored(self.args.port_out, 'yellow')))
            self.opened_socks.append(out_sock)

            self.logger.info(
                'input %s (%s) \t output %s (%s)\t control over %s (%s)' %
                (colored(in_addr, 'yellow'), self.args.socket_in,
                 colored(out_addr, 'yellow'), self.args.socket_out,
                 colored(ctrl_addr, 'yellow'), SocketType.PAIR_BIND))
            return ctx, in_sock, out_sock, ctrl_sock
        except zmq.error.ZMQError as ex:
            self.close()
            raise ex

    def _get_zmq_ctx(self):
        return zmq.Context()

    def __enter__(self):
        # time.sleep(.1)  # timeout handshake is unnecessary at the Pod level, it is only required for gateway
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close all sockets and shutdown the ZMQ context associated to this `Zmqlet`. """
        self.close_sockets()
        if hasattr(self, 'ctx'):
            self.ctx.term()
        self.print_stats()

    def print_stats(self):
        """Print out the network stats of of itself """
        self.logger.info(f'#sent: {self.msg_sent} '
                         f'#recv: {self.msg_recv} '
                         f'sent_size: {get_readable_size(self.bytes_sent)} '
                         f'recv_size: {get_readable_size(self.bytes_recv)}')
        profile_logger.debug({'msg_sent': self.msg_sent,
                              'msg_recv': self.msg_recv,
                              'bytes_sent': self.bytes_sent,
                              'bytes_recv': self.bytes_recv})

    def send_message(self, msg: 'jina_pb2.Message'):
        """Send a message via the output socket

        :param msg: the protobuf message to send
        """
        # choose output sock

        _req = getattr(msg.request, msg.request.WhichOneof('body'))
        _req_type = type(_req)

        if is_data_request(_req):
            o_sock = self.out_sock
        else:
            o_sock = self.ctrl_sock

        self.bytes_sent += send_message(o_sock, msg, **self.send_recv_kwargs)
        self.msg_sent += 1

        if o_sock == self.out_sock and self.in_sock.type == zmq.DEALER:
            self.send_idle(msg)

    def send_idle(self, msg: Optional['jina_pb2.Message'] = None):
        """Tell the upstream router this dealer is idle """
        if msg:
            msg.request.control.command = jina_pb2.Request.ControlRequest.IDLE
        else:
            req = jina_pb2.Request()
            req.control.command = jina_pb2.Request.ControlRequest.IDLE
            msg = add_envelope(req, self.name, self.args.identity)
        self.bytes_sent += send_message(self.in_sock, msg, **self.send_recv_kwargs)
        self.msg_sent += 1
        self.logger.debug('idle and i told the router')

    def recv_message(self, callback: Callable[['jina_pb2.Message'], None] = None) -> 'jina_pb2.Message':
        """Receive a protobuf message from the input socket

        :param callback: the callback function, which modifies the recevied message inplace.
        :return: the received (and modified) protobuf message
        """
        i_sock = self._pull()
        if i_sock is not None:
            msg, num_bytes = recv_message(i_sock, **self.send_recv_kwargs)
            self.bytes_recv += num_bytes
            self.msg_recv += 1
            if callback:
                return callback(msg)

    def clear_stats(self):
        """Reset the internal counter of send and receive bytes to zero. """
        self.bytes_recv = 0
        self.bytes_sent = 0
        self.msg_recv = 0
        self.msg_sent = 0


class AsyncZmqlet(Zmqlet):
    """An async vesion of :class:`Zmqlet`.
    The :func:`send_message` and :func:`recv_message` works in the async manner.
    """

    def _get_zmq_ctx(self):
        return zmq.asyncio.Context()

    async def send_message(self, msg: 'jina_pb2.Message', sleep: float = 0, **kwargs):
        """Send a protobuf message in async via the output socket

        :param msg: the protobuf message to send
        :param sleep: the sleep time of every two sends in millisecond.
                A near-zero value could result in bad load balancing in the proceeding pods.
        """
        # await asyncio.sleep(sleep)  # preventing over-speed sending
        try:
            num_bytes = await send_message_async(self.out_sock, msg, **self.send_recv_kwargs)
            self.bytes_sent += num_bytes
            self.msg_sent += 1
        except (asyncio.CancelledError, TypeError) as ex:
            self.logger.error(f'{ex}, gateway cancelled?')

    async def recv_message(self, callback: Callable[['jina_pb2.Message'], None] = None) -> 'jina_pb2.Message':
        try:
            msg, num_bytes = await recv_message_async(self.in_sock, **self.send_recv_kwargs)
            self.bytes_recv += num_bytes
            self.msg_recv += 1
            if callback:
                return callback(msg)
        except (asyncio.CancelledError, TypeError) as ex:
            self.logger.error(f'{ex}, gateway cancelled?')

    def __enter__(self):
        time.sleep(.2)  # sleep a bit until handshake is done
        return self


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


def send_message(sock: 'zmq.Socket', msg: 'jina_pb2.Message', timeout: int = -1,
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
    except asyncio.CancelledError:
        default_logger.error('all gateway tasks are cancelled')
    except Exception as ex:
        raise ex
    finally:
        try:
            sock.setsockopt(zmq.SNDTIMEO, -1)
        except zmq.error.ZMQError:
            pass

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


async def send_message_async(sock: 'zmq.Socket', msg: 'jina_pb2.Message', timeout: int = -1,
                             array_in_pb: bool = False, compress_hwm: int = -1, compress_lwm: float = 1.,
                             **kwargs) -> int:
    """Send a protobuf message to a socket in async manner

    :param sock: the target socket to send
    :param msg: the protobuf message
    :param timeout: waiting time (in seconds) for sending
    :param array_in_pb: send the numpy array within the protobuf message, this often yields worse network efficiency
    :param compress_hwm: message bigger than this size (in bytes) will be compressed by lz4 algorithm, set to -1 to disable this feature.
    :param compress_lwm: the low watermark that enables the sending of a compressed message.
    :return: the size (in bytes) of the sent message
    """
    try:
        _msg, num_bytes = _prep_send_msg(array_in_pb, compress_hwm, compress_lwm, msg, sock, timeout)

        await sock.send_multipart(_msg)

        return num_bytes
    except zmq.error.Again:
        raise TimeoutError(
            'cannot send message to sock %s after timeout=%dms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? ' % (
                sock, timeout))
    except zmq.error.ZMQError as ex:
        default_logger.critical(ex)
    except asyncio.CancelledError:
        default_logger.error('all gateway tasks are cancelled')
    except Exception as ex:
        raise ex
    finally:
        try:
            sock.setsockopt(zmq.SNDTIMEO, -1)
        except zmq.error.ZMQError:
            pass


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


async def recv_message_async(sock: 'zmq.Socket', timeout: int = -1, check_version: bool = False, **kwargs) -> Tuple[
    'jina_pb2.Message', int]:
    """ Receive a protobuf message from a socket in async manner

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

        msg_data = await sock.recv_multipart()

        return _prepare_recv_msg(sock, msg_data, check_version)

    except zmq.error.Again:
        raise TimeoutError(
            'no response from sock %s after timeout=%dms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? ' % (
                sock, timeout))
    except zmq.error.ZMQError as ex:
        default_logger.critical(ex)
    except asyncio.CancelledError:
        default_logger.error('all gateway tasks are cancelled')
    except Exception as ex:
        raise ex
    finally:
        try:
            sock.setsockopt(zmq.RCVTIMEO, -1)
        except zmq.error.ZMQError:
            pass


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


def _prepare_recv_msg(sock, msg_data, check_version: bool):
    if sock.type == zmq.DEALER:
        # dealer consumes the first part of the message as id, we need to prepend it back
        msg_data = [' '] + msg_data
    elif sock.type == zmq.ROUTER:
        # the router appends dealer id when receive it, we need to remove it
        msg_data.pop(0)

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
            raise ValueError('This directory for sockets ({}) does not seems to exist.'.format(tmp))
        tmp = os.path.join(tmp, get_random_identity())
    except KeyError:
        tmp = tempfile.NamedTemporaryFile().name
    return 'ipc://%s' % tmp


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
                    'host is set from %s to %s as the socket is in BIND type' % (host, __default_host__))
                host = __default_host__
            if port is None:
                sock.bind_to_random_port('tcp://%s' % host)
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
