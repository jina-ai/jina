__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
import asyncio
import os
import tempfile
import time
from typing import List, Callable, Union, Tuple, Optional

import zmq
import zmq.asyncio
from zmq.eventloop.zmqstream import ZMQStream
from zmq.ssh import tunnel_connection

from ... import __default_host__, Request
from ...enums import SocketType
from ...helper import colored, random_identity, get_readable_size, get_or_reuse_loop
from ...importer import ImportExtensions
from ...logging import default_logger, profile_logger, JinaLogger
from ...types.message import Message
from ...types.message.common import ControlMessage


class Zmqlet:
    """A `Zmqlet` object can send/receive data to/from ZeroMQ socket and invoke callback function. It
    has three sockets for input, output and control.

    .. warning::
        Starting from v0.3.6, :class:`ZmqStreamlet` replaces :class:`Zmqlet` as one of the key components in :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime`.
        It requires :mod:`tornado` and :mod:`uvloop` to be installed.
    """

    def __init__(self, args: 'argparse.Namespace', logger: 'JinaLogger' = None, ctrl_addr: str = None):
        """

        :param args: the parsed arguments from the CLI
        :param logger: the logger to use
        """
        self.args = args
        self.identity = self.args.identity
        self.name = args.name or self.__class__.__name__
        self.logger = logger
        self.send_recv_kwargs = vars(args)
        if ctrl_addr:
            self.ctrl_addr = ctrl_addr
            self.ctrl_with_ipc = self.ctrl_addr.startswith('ipc://')
        else:
            self.ctrl_addr, self.ctrl_with_ipc = self.get_ctrl_address(args.host, args.port_ctrl, args.ctrl_with_ipc)

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
    def get_ctrl_address(host: Optional[str], port_ctrl: Optional[str], ctrl_with_ipc: bool) -> Tuple[str, bool]:
        """Get the address of the control socket

        :param host: the host in the arguments
        :param port_ctrl: the control port
        :param ctrl_with_ipc: a bool of whether using IPC protocol for controlling
        :return: A tuple of two pieces:

            - a string of control address
            - a bool of whether using IPC protocol for controlling

        """

        ctrl_with_ipc = (os.name != 'nt') and ctrl_with_ipc
        if ctrl_with_ipc:
            return _get_random_ipc(), ctrl_with_ipc
        else:
            host_out = host
            if '@' in host_out:
                # user@hostname
                host_out = host_out.split('@')[-1]
            else:
                host_out = host_out
            return f'tcp://{host_out}:{port_ctrl}', ctrl_with_ipc

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

        self.logger.debug('setting up sockets...')
        try:
            if self.ctrl_with_ipc:
                ctrl_sock, ctrl_addr = _init_socket(ctx, self.ctrl_addr, None, SocketType.PAIR_BIND,
                                                    use_ipc=self.ctrl_with_ipc)
            else:
                ctrl_sock, ctrl_addr = _init_socket(ctx, __default_host__, self.args.port_ctrl, SocketType.PAIR_BIND)
            self.logger.debug(f'control over {colored(ctrl_addr, "yellow")}')

            in_sock, in_addr = _init_socket(ctx, self.args.host_in, self.args.port_in, self.args.socket_in,
                                            self.identity,
                                            ssh_server=self.args.ssh_server,
                                            ssh_keyfile=self.args.ssh_keyfile,
                                            ssh_password=self.args.ssh_password)
            self.logger.debug(f'input {self.args.host_in}:{colored(self.args.port_in, "yellow")}')

            out_sock, out_addr = _init_socket(ctx, self.args.host_out, self.args.port_out, self.args.socket_out,
                                              self.identity,
                                              ssh_server=self.args.ssh_server,
                                              ssh_keyfile=self.args.ssh_keyfile,
                                              ssh_password=self.args.ssh_password
                                              )
            self.logger.debug(f'output {self.args.host_out}:{colored(self.args.port_out, "yellow")}')

            self.logger.info(
                f'input {colored(in_addr, "yellow")} ({self.args.socket_in.name}) '
                f'output {colored(out_addr, "yellow")} ({self.args.socket_out.name}) '
                f'control over {colored(ctrl_addr, "yellow")} ({SocketType.PAIR_BIND.name})')

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
        """Close all sockets and shutdown the ZMQ context associated to this `Zmqlet`.

        .. note::
            This method is idempotent.

        """
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

    def send_message(self, msg: 'Message'):
        """Send a message via the output socket

        :param msg: the protobuf message to send
        """
        # choose output sock

        if msg.is_data_request:
            o_sock = self.out_sock
        else:
            o_sock = self.ctrl_sock

        self.bytes_sent += send_message(o_sock, msg, **self.send_recv_kwargs)
        self.msg_sent += 1

        if o_sock == self.out_sock and self.in_sock_type == zmq.DEALER:
            self.send_idle()

    def send_idle(self):
        """Tell the upstream router this dealer is idle """
        msg = ControlMessage('IDLE', pod_name=self.name, identity=self.identity)
        self.bytes_sent += send_message(self.in_sock, msg, **self.send_recv_kwargs)
        self.msg_sent += 1
        self.logger.debug('idle and i told the router')

    def recv_message(self, callback: Callable[['Message'], 'Message'] = None) -> 'Message':
        """Receive a protobuf message from the input socket

        :param callback: the callback function, which modifies the recevied message inplace.
        :return: the received (and modified) protobuf message
        """
        i_sock = self._pull()
        if i_sock is not None:
            msg = recv_message(i_sock, **self.send_recv_kwargs)
            self.bytes_recv += msg.size
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

    async def send_message(self, msg: 'Message', sleep: float = 0, **kwargs):
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
            self.logger.error(f'sending message error: {ex!r}, gateway cancelled?')

    async def recv_message(self, callback: Callable[['Message'], Union['Message', 'Request']] = None) -> 'Message':
        try:
            msg = await recv_message_async(self.in_sock, **self.send_recv_kwargs)
            self.bytes_recv += msg.size
            self.msg_recv += 1
            if callback:
                return callback(msg)
        except (asyncio.CancelledError, TypeError) as ex:
            self.logger.error(f'receiving message error: {ex!r}, gateway cancelled?')

    def __enter__(self):
        time.sleep(.2)  # sleep a bit until handshake is done
        return self


class ZmqStreamlet(Zmqlet):
    """A :class:`ZmqStreamlet` object can send/receive data to/from ZeroMQ stream and invoke callback function. It
    has three sockets for input, output and control.

    .. warning::
        Starting from v0.3.6, :class:`ZmqStreamlet` replaces :class:`Zmqlet` as one of the key components in :class:`jina.peapods.runtime.BasePea`.
        It requires :mod:`tornado` and :mod:`uvloop` to be installed.
    """

    def register_pollin(self):
        with ImportExtensions(required=True):
            import tornado.ioloop
            get_or_reuse_loop()
            self.io_loop = tornado.ioloop.IOLoop.current()
        self.in_sock = ZMQStream(self.in_sock, self.io_loop)
        self.out_sock = ZMQStream(self.out_sock, self.io_loop)
        self.ctrl_sock = ZMQStream(self.ctrl_sock, self.io_loop)
        self.in_sock.stop_on_recv()

    def close(self):
        """Close all sockets and shutdown the ZMQ context associated to this `Zmqlet`.

        .. note::
            This method is idempotent.
        """
        if not self.is_closed:
            # wait until the close signal is received
            time.sleep(.01)
            for s in self.opened_socks:
                s.flush()
            super().close()
            if hasattr(self, 'io_loop'):
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
                    self.logger.error(f'failed to stop. {e!r}')

    def pause_pollin(self):
        """Remove :attr:`in_sock` from the poller """
        self.in_sock.stop_on_recv()

    def resume_pollin(self):
        """Put :attr:`in_sock` back to the poller """
        self.in_sock.on_recv(self._in_sock_callback)

    def start(self, callback: Callable[['Message'], 'Message']):
        def _callback(msg, sock_type):
            msg = _parse_from_frames(sock_type, msg)
            self.bytes_recv += msg.size
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


def send_ctrl_message(address: str, cmd: str, timeout: int) -> 'Message':
    """Send a control message to a specific address and wait for the response

    :param address: the socket address to send
    :param cmd: the control command to send
    :param timeout: the waiting time (in ms) for the response
    """
    # control message is short, set a timeout and ask for quick response
    with zmq.Context() as ctx:
        ctx.setsockopt(zmq.LINGER, 0)
        sock, _ = _init_socket(ctx, address, None, SocketType.PAIR_CONNECT)
        msg = ControlMessage(cmd)
        send_message(sock, msg, timeout)
        r = None
        try:
            r = recv_message(sock, timeout)
        except TimeoutError:
            pass
        finally:
            sock.close()
        return r


def send_message(sock: Union['zmq.Socket', 'ZMQStream'], msg: 'Message', timeout: int = -1, **kwargs) -> int:
    """Send a protobuf message to a socket

    :param sock: the target socket to send
    :param msg: the protobuf message
    :param timeout: waiting time (in seconds) for sending
    :return: the size (in bytes) of the sent message
    """
    num_bytes = 0
    try:
        _prep_send_socket(sock, timeout)
        sock.send_multipart(msg.dump())
        num_bytes = msg.size
    except zmq.error.Again:
        raise TimeoutError(
            f'cannot send message to sock {sock} after timeout={timeout}ms, please check the following:'
            'is the server still online? is the network broken? are "port" correct?')
    except zmq.error.ZMQError as ex:
        default_logger.critical(ex)
    finally:
        try:
            sock.setsockopt(zmq.SNDTIMEO, -1)
        except zmq.error.ZMQError:
            pass

    return num_bytes


def _prep_send_socket(sock, timeout):
    if timeout > 0:
        sock.setsockopt(zmq.SNDTIMEO, timeout)
    else:
        sock.setsockopt(zmq.SNDTIMEO, -1)


def _prep_recv_socket(sock, timeout):
    if timeout > 0:
        sock.setsockopt(zmq.RCVTIMEO, timeout)
    else:
        sock.setsockopt(zmq.RCVTIMEO, -1)


async def send_message_async(sock: 'zmq.Socket', msg: 'Message', timeout: int = -1,
                             **kwargs) -> int:
    """Send a protobuf message to a socket in async manner

    :param sock: the target socket to send
    :param msg: the protobuf message
    :param timeout: waiting time (in seconds) for sending
    :return: the size (in bytes) of the sent message
    """
    try:
        _prep_send_socket(sock, timeout)
        await sock.send_multipart(msg.dump())
        return msg.size
    except zmq.error.Again:
        raise TimeoutError(
            f'cannot send message to sock {sock} after timeout={timeout}ms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? ')
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


def recv_message(sock: 'zmq.Socket', timeout: int = -1, **kwargs) -> 'Message':
    """ Receive a protobuf message from a socket

    :param sock: the socket to pull from
    :param timeout: max wait time for pulling, -1 means wait forever
    :return: a tuple of two pieces

            - the received protobuf message
            - the size of the message in bytes
    """
    try:
        _prep_recv_socket(sock, timeout)
        msg_data = sock.recv_multipart()
        return _parse_from_frames(sock.type, msg_data)

    except zmq.error.Again:
        raise TimeoutError(
            f'no response from sock {sock} after timeout={timeout}ms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? ')
    except Exception as ex:
        raise ex
    finally:
        sock.setsockopt(zmq.RCVTIMEO, -1)


async def recv_message_async(sock: 'zmq.Socket', timeout: int = -1,
                             **kwargs) -> 'Message':
    """ Receive a protobuf message from a socket in async manner

    :param sock: the socket to pull from
    :param timeout: max wait time for pulling, -1 means wait forever
    :return: a tuple of two pieces

            - the received protobuf message
            - the size of the message in bytes
    """

    try:
        _prep_recv_socket(sock, timeout)
        msg_data = await sock.recv_multipart()
        return _parse_from_frames(sock.type, msg_data)

    except zmq.error.Again:
        raise TimeoutError(
            f'no response from sock {sock} after timeout={timeout}ms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? ')
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


def _parse_from_frames(sock_type, frames: List[bytes]) -> 'Message':
    """
    Build :class:`Message` from a list of frames.

    The list of frames (has length >=3) has the following structure:

        - offset 0: the client id, can be empty
        - offset 1: is the offset 2 frame compressed
        - offset 2: the body of the serialized protobuf message

    :param sock_type: the recv socket type
    :param frames: list of bytes to parse from
    :return: a :class:`Message` object
    """
    if sock_type == zmq.DEALER:
        # dealer consumes the first part of the message as id, we need to prepend it back
        frames = [b' '] + frames
    elif sock_type == zmq.ROUTER:
        # the router appends dealer id when receive it, we need to remove it
        frames.pop(0)

    return Message(frames[1], frames[2])


def _get_random_ipc() -> str:
    """Get a random IPC address for control port """
    try:
        tmp = os.environ['JINA_IPC_SOCK_TMP']
        if not os.path.exists(tmp):
            raise ValueError(f'This directory for sockets ({tmp}) does not seems to exist.')
        tmp = os.path.join(tmp, random_identity())
    except KeyError:
        tmp = tempfile.NamedTemporaryFile().name
    return f'ipc://{tmp}'


def _init_socket(ctx: 'zmq.Context', host: str, port: Optional[int],
                 socket_type: 'SocketType', identity: str = None,
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
                except zmq.error.ZMQError:
                    default_logger.error(f'error when binding port {port} to {host}, this port is occupied.')
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
