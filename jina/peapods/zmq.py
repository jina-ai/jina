__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import asyncio
import os
import sys
import tempfile
import time
from typing import List, Callable, Optional, Union, Tuple, Iterable

import zmq
import zmq.asyncio
from zmq.eventloop.zmqstream import ZMQStream
from zmq.ssh import tunnel_connection

from .. import __default_host__
from ..enums import SocketType
from ..excepts import MismatchedVersion
from ..helper import colored, get_random_identity, get_readable_size, use_uvloop
from ..logging import default_logger, profile_logger, JinaLogger
from ..proto import jina_pb2, is_data_request

if False:
    # fix type-hint complain for sphinx and flake
    import argparse
    from ..proto.jina_pb2 import Message

use_uvloop()


class Zmqlet:
    """A `Zmqlet` object can send/receive data to/from ZeroMQ socket and invoke callback function. It
    has three sockets for input, output and control.

    .. warning::
        Starting from v0.3.6, :class:`ZmqStreamlet` replaces :class:`Zmqlet` as one of the key components in :class:`jina.peapods.pea.BasePea`.
        It requires :mod:`tornado` and :mod:`uvloop` to be installed.
    """

    def __init__(self, args: 'argparse.Namespace', logger: 'JinaLogger' = None):
        """

        :param args: the parsed arguments from the CLI
        :param logger: the logger to use
        """
        self.args = args
        self.name = args.name or self.__class__.__name__
        self.logger = logger
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
        self.bytes_sent = 0
        self.bytes_recv = 0
        self.msg_recv = 0
        self.msg_sent = 0
        self.is_closed = False
        self.opened_socks = []  # this must be here for `close()`
        self.ctx, self.in_sock, self.out_sock, self.ctrl_sock = self.init_sockets()
        self.register_pollin()

        self.opened_socks.extend([self.in_sock, self.out_sock, self.ctrl_sock])
        if self.in_sock_type == zmq.DEALER:
            self.send_idle()

    def register_pollin(self):
        self.poller = zmq.Poller()
        self.poller.register(self.in_sock, zmq.POLLIN)
        self.poller.register(self.ctrl_sock, zmq.POLLIN)
        if self.out_sock_type == zmq.ROUTER:
            self.poller.register(self.out_sock, zmq.POLLIN)

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
            self.logger.debug(f'control over {colored(ctrl_addr, "yellow")}')

            in_sock, in_addr = _init_socket(ctx, self.args.host_in, self.args.port_in, self.args.socket_in,
                                            self.args.identity,
                                            ssh_server=self.args.ssh_server,
                                            ssh_keyfile=self.args.ssh_keyfile,
                                            ssh_password=self.args.ssh_password)
            self.logger.debug(f'input {self.args.host_in}:{colored(self.args.port_in, "yellow")}')

            out_sock, out_addr = _init_socket(ctx, self.args.host_out, self.args.port_out, self.args.socket_out,
                                              self.args.identity,
                                              ssh_server=self.args.ssh_server,
                                              ssh_keyfile=self.args.ssh_keyfile,
                                              ssh_password=self.args.ssh_password
                                              )
            self.logger.debug(f'output {self.args.host_out}:{colored(self.args.port_out, "yellow")}')

            self.logger.info(
                'input %s (%s) \t output %s (%s)\t control over %s (%s)' %
                (colored(in_addr, 'yellow'), self.args.socket_in,
                 colored(out_addr, 'yellow'), self.args.socket_out,
                 colored(ctrl_addr, 'yellow'), SocketType.PAIR_BIND))

            self.in_sock_type = in_sock.type
            self.out_sock_type = out_sock.type
            self.ctrl_sock_type = ctrl_sock.type

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
        if not self.is_closed:
            self.is_closed = True
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
        profile_logger.info({'msg_sent': self.msg_sent,
                             'msg_recv': self.msg_recv,
                             'bytes_sent': self.bytes_sent,
                             'bytes_recv': self.bytes_recv})

    def send_message(self, msg: 'jina_pb2.Message'):
        """Send a message via the output socket

        :param msg: the protobuf message to send
        """
        # choose output sock

        _req = getattr(msg.request, msg.request.WhichOneof('body'))

        if is_data_request(_req):
            o_sock = self.out_sock
        else:
            o_sock = self.ctrl_sock

        self.bytes_sent += send_message(o_sock, msg, **self.send_recv_kwargs)
        self.msg_sent += 1

        if o_sock == self.out_sock and self.in_sock_type == zmq.DEALER:
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
            self.logger.error(f'sending message error: {ex}, gateway cancelled?')

    async def recv_message(self, callback: Callable[['jina_pb2.Message'], None] = None) -> 'jina_pb2.Message':
        try:
            msg, num_bytes = await recv_message_async(self.in_sock, **self.send_recv_kwargs)
            self.bytes_recv += num_bytes
            self.msg_recv += 1
            if callback:
                return callback(msg)
        except (asyncio.CancelledError, TypeError) as ex:
            self.logger.error(f'receiving message error: {ex}, gateway cancelled?')

    def __enter__(self):
        time.sleep(.2)  # sleep a bit until handshake is done
        return self


class ZmqStreamlet(Zmqlet):
    """A :class:`ZmqStreamlet` object can send/receive data to/from ZeroMQ stream and invoke callback function. It
    has three sockets for input, output and control.

    .. warning::
        Starting from v0.3.6, :class:`ZmqStreamlet` replaces :class:`Zmqlet` as one of the key components in :class:`jina.peapods.pea.BasePea`.
        It requires :mod:`tornado` and :mod:`uvloop` to be installed.
    """

    def register_pollin(self):
        use_uvloop()
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
        try:
            import tornado.ioloop
            self.io_loop = tornado.ioloop.IOLoop.current()
        except (ModuleNotFoundError, ImportError):
            self.logger.error('Since v0.3.6 Jina requires "tornado" as a base dependency, '
                              'we use its I/O event loop for non-blocking sockets. '
                              'Please try reinstall via "pip install -U jina" to include this dependency')
            raise
        self.in_sock = ZMQStream(self.in_sock, self.io_loop)
        self.out_sock = ZMQStream(self.out_sock, self.io_loop)
        self.ctrl_sock = ZMQStream(self.ctrl_sock, self.io_loop)
        self.in_sock.stop_on_recv()

    def close(self):
        """Close all sockets and shutdown the ZMQ context associated to this `Zmqlet`. """
        if not self.is_closed:
            # wait until the close signal is received
            time.sleep(.01)
            for s in self.opened_socks:
                s.flush()
            super().close()
            try:
                self.io_loop.stop()
                # Replace handle events function, to skip
                # None event after sockets are closed.
                if hasattr(self.in_sock, '_handle_events'):
                    self.in_sock._handle_events = lambda *args, **kwargs: None
                if hasattr(self.out_sock, '_handle_events'):
                    self.out_sock._handle_events = lambda *args, **kwargs: None
                if hasattr(self.ctrl_sock, '_handle_events'):
                    self.ctrl_sock._handle_events = lambda *args, **kwargs: None
            except AttributeError as e:
                self.logger.error(f'failed to stop. {e}')

    def pause_pollin(self):
        """Remove :attr:`in_sock` from the poller """
        self.in_sock.stop_on_recv()

    def resume_pollin(self):
        """Put :attr:`in_sock` back to the poller """
        self.in_sock.on_recv(self._in_sock_callback)

    def start(self, callback: Callable[['jina_pb2.Message'], None]):
        def _callback(msg, sock_type):
            msg, num_bytes = _parse_from_frames(sock_type, msg, self.args.check_version)
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


def send_message(sock: Union['zmq.Socket', 'ZMQStream'], msg: 'jina_pb2.Message', timeout: int = -1,
                 compress_hwm: float = -1, compress_lwm: float = 1., **kwargs) -> int:
    """Send a protobuf message to a socket

    :param sock: the target socket to send
    :param msg: the protobuf message
    :param timeout: waiting time (in seconds) for sending
    :param compress_hwm: message bigger than this size (in bytes) will be compressed by lz4 algorithm, set to -1 to disable this feature.
    :param compress_lwm: the low watermark that enables the sending of a compressed message.
    :return: the size (in bytes) of the sent message
    """
    num_bytes = 0
    try:
        _msg, num_bytes = _prep_send_msg(compress_hwm, compress_lwm, msg, sock, timeout)

        sock.send_multipart(_msg)
    except zmq.error.Again:
        raise TimeoutError(
            'cannot send message to sock %s after timeout=%dms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? ' % (
                sock, timeout))
    except zmq.error.ZMQError as ex:
        default_logger.critical(ex)
    finally:
        try:
            sock.setsockopt(zmq.SNDTIMEO, -1)
        except zmq.error.ZMQError:
            pass

    return num_bytes


def _prep_send_msg(compress_hwm, compress_lwm, msg, sock, timeout):
    if timeout > 0:
        sock.setsockopt(zmq.SNDTIMEO, timeout)
    else:
        sock.setsockopt(zmq.SNDTIMEO, -1)
    return _serialize_to_frames(msg.envelope.receiver_id,
                                msg,
                                compress_hwm,
                                compress_lwm)


async def send_message_async(sock: 'zmq.Socket', msg: 'jina_pb2.Message', timeout: int = -1,
                             compress_hwm: float = -1, compress_lwm: float = 1.,
                             **kwargs) -> int:
    """Send a protobuf message to a socket in async manner

    :param sock: the target socket to send
    :param msg: the protobuf message
    :param timeout: waiting time (in seconds) for sending
    :param compress_hwm: message bigger than this size (in bytes) will be compressed by lz4 algorithm, set to -1 to disable this feature.
    :param compress_lwm: the low watermark that enables the sending of a compressed message.
    :return: the size (in bytes) of the sent message
    """
    try:
        _msg, num_bytes = _prep_send_msg(compress_hwm, compress_lwm, msg, sock, timeout)

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

        return _parse_from_frames(sock.type, msg_data, check_version)

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

        return _parse_from_frames(sock.type, msg_data, check_version)

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


def _serialize_to_frames(client_id, msg: 'jina_pb2.Message',
                         compress_hwm: float, compress_lwm: float) -> Tuple[List[bytes], int]:
    """
    Serialize a :class:`jina_pb2.Message` object into a list of frames. The list of frames (has length >=3) has the following structure:

        - offset 0: the client id, can be empty
        - offset 1: is the offset 2 frame compressed
        - offset 2: the body of the serialized protobuf message

    :param client_id: the client id
    :param msg: the protobuf message object to be serialized
    :param compress_hwm: message bigger than this size (in bytes) will be compressed by lz4 algorithm, set to -1 to disable this feature.
    :param compress_lwm: the low watermark that enables the sending of a compressed message.
    :return:
    """
    _body = [msg.SerializeToString()]

    _size_before = sum(sys.getsizeof(m) for m in _body)
    if _size_before > compress_hwm > 0:
        import lz4.frame
        body = [lz4.frame.compress(m) for m in _body]
        is_compressed = b'1'
        _size_after = sum(sys.getsizeof(m) for m in body)
        rate = _size_after / _size_before
        default_logger.debug(f'compressed, before: {_size_before} after: {_size_after}, '
                             f'ratio: {(_size_after / _size_before * 100):.0f}%')
        if rate > compress_lwm:
            body = _body
            is_compressed = b'0'
            default_logger.debug(f'ineffective compression as the rate {rate:.2f} is higher than {compress_lwm}')
    else:
        body = _body
        is_compressed = b'0'

    if isinstance(client_id, str):
        client_id = client_id.encode()
    frames = [client_id, is_compressed] + body
    num_bytes = sum(sys.getsizeof(m) for m in frames)
    return frames, num_bytes


def _parse_from_frames(sock_type, frames: List[bytes], check_version: bool) -> Tuple['jina_pb2.Message', int]:
    """
    Build :class:`jina_pb2.Message` from a list of frames.

    The list of frames (has length >=3) has the following structure:

        - offset 0: the client id, can be empty
        - offset 1: is the offset 2 frame compressed
        - offset 2: the body of the serialized protobuf message

    :param sock_type: the recv socket type
    :param frames: list of bytes to parse from
    :param check_version: check if the jina, protobuf version info in the incoming message consists with the local versions
    :return: a :class:`jina_pb2.Message` object and the size of the frames (in bytes)
    """
    if sock_type == zmq.DEALER:
        # dealer consumes the first part of the message as id, we need to prepend it back
        frames = [b' '] + frames
    elif sock_type == zmq.ROUTER:
        # the router appends dealer id when receive it, we need to remove it
        frames.pop(0)

    # count the size before decompress
    num_bytes = sum(sys.getsizeof(m) for m in frames)

    if frames[1] == b'1':
        # body message is compressed
        import lz4.frame
        for l in range(2, len(frames)):
            frames[l] = lz4.frame.decompress(frames[l])

    msg = jina_pb2.Message()

    msg.ParseFromString(frames[2])

    if check_version:
        _check_msg_version(msg)

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
                 socket_type: 'SocketType', identity: 'str' = None,
                 use_ipc: bool = False, ssh_server: str = None,
                 ssh_keyfile: str = None, ssh_password: str = None) -> Tuple['zmq.Socket', str]:
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
                    sock.bind(f'tcp://{host}:{port}')
                except zmq.error.ZMQError as ex:
                    default_logger.error(f'error when binding port {port} to {host}')
                    raise
    else:
        if port is None:
            address = host
        else:
            address = f'tcp://{host}:{port}'

        # note that ssh only takes effect on CONNECT, not BIND
        # that means control socket setup does not need ssh
        if ssh_server:
            tunnel_connection(sock, address, ssh_server, ssh_keyfile, ssh_password)
        else:
            sock.connect(address)

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


def _extract_bytes_from_documents(docs: Iterable['jina_pb2.Document']) -> Tuple:
    doc_bytes = []
    chunk_bytes = []
    chunk_byte_type = b''

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


def _fill_buffer_to_documents(msg_data: List[bytes], docs: Iterable['jina_pb2.Document'], offset: int = 3):
    """
    Message comes split in different parts (that's why it comes as an Iterable, Each element
            can be any sendable object (Frame, bytes, buffer-providers)):
    Parts 0 and 1 contain information about potentially the receiver (if DEALER) and whether it is compressed or not.
    Part 2 has a msg representation.
    Part 3 (offset = 3) has the encoded name of the type of chunk bytes (Limitation: Only consider one chunk type for complete message)
    Parts 4 and 5 contain the length of the doc_bytes and chunk_bytes respectively.
    Then N number of Parts come with the doc bytes
    Then M number of Parts com with the chunk bytes (chunk bytes length is twice the number of chunks in the message)
    """
    chunk_byte_type = msg_data[offset].decode()
    doc_bytes_len = int(msg_data[offset + 1])
    chunk_bytes_len = int(msg_data[offset + 2])
    doc_bytes = msg_data[(offset + 3):(offset + 3 + doc_bytes_len)]
    chunk_bytes = msg_data[(offset + 3 + doc_bytes_len):]

    if len(chunk_bytes) != chunk_bytes_len:
        raise ValueError('"chunk_bytes_len"=%d in message, but the actual length is %d' % (
            chunk_bytes_len, len(chunk_bytes)))

    c_idx = 0
    d_idx = 0
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
