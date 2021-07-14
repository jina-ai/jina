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

from ..networking import get_connect_host
from ... import __default_host__
from ...enums import SocketType
from ...helper import colored, random_identity, get_readable_size, get_or_reuse_loop
from ...importer import ImportExtensions
from ...logging.logger import JinaLogger
from ...logging.predefined import default_logger
from ...proto import jina_pb2
from ...types.message import Message
from ...types.message.common import ControlMessage
from ...types.request import Request
from ...types.routing.table import RoutingTable

if False:
    import multiprocessing
    import threading


class Zmqlet:
    """A `Zmqlet` object can send/receive data to/from ZeroMQ socket and invoke callback function. It
    has three sockets for input, output and control.

    :param args: the parsed arguments from the CLI
    :param logger: the logger to use
    :param ctrl_addr: control address

    .. warning::
        Starting from v0.3.6, :class:`ZmqStreamlet` replaces :class:`Zmqlet` as one of the key components in :class:`jina.peapods.runtimes.zmq.zed.ZEDRuntime`.
        It requires :mod:`tornado` and :mod:`uvloop` to be installed.
    """

    def __init__(
        self,
        args: 'argparse.Namespace',
        logger: Optional['JinaLogger'] = None,
        ctrl_addr: Optional[str] = None,
    ):
        self.args = args

        if args.zmq_identity:
            self.identity = args.zmq_identity
        else:
            self.identity = random_identity()
        self.name = args.name or self.__class__.__name__
        self.logger = logger
        self.send_recv_kwargs = vars(args)
        if ctrl_addr:
            self.ctrl_addr = ctrl_addr
            self.ctrl_with_ipc = self.ctrl_addr.startswith('ipc://')
        else:
            self.ctrl_addr, self.ctrl_with_ipc = self.get_ctrl_address(
                args.host, args.port_ctrl, args.ctrl_with_ipc
            )

        self.bytes_sent = 0
        self.bytes_recv = 0
        self.msg_recv = 0
        self.msg_sent = 0
        self.is_closed = False
        self.is_polling_paused = False
        self.in_sock_type = None
        self.out_sock_type = None
        self.ctrl_sock_type = None
        self.opened_socks = []  # this must be here for `close()`
        (
            self.ctx,
            self.in_sock,
            self.out_sock,
            self.ctrl_sock,
            self.in_connect_sock,
        ) = self._init_sockets()

        self.in_sock_type = self.in_sock.type
        self.out_sock_type = self.out_sock.type
        self.ctrl_sock_type = self.ctrl_sock.type

        self._register_pollin()
        self.opened_socks.extend([self.in_sock, self.out_sock, self.ctrl_sock])
        if self.in_connect_sock is not None:
            self.opened_socks.append(self.in_connect_sock)

        self.out_sockets = {}
        self._active = True

    def _register_pollin(self):
        """Register :attr:`in_sock`, :attr:`ctrl_sock` and :attr:`out_sock` (if :attr:`out_sock_type` is zmq.ROUTER)
        in poller."""
        self.poller = zmq.Poller()
        self.poller.register(self.in_sock, zmq.POLLIN)
        self.poller.register(self.ctrl_sock, zmq.POLLIN)
        if self.out_sock_type == zmq.ROUTER and not self.args.dynamic_routing_out:
            self.poller.register(self.out_sock, zmq.POLLIN)
        if self.in_connect_sock is not None:
            self.poller.register(self.in_connect_sock, zmq.POLLIN)

    def pause_pollin(self):
        """Remove :attr:`in_sock` from the poller """
        self.poller.unregister(self.in_sock)

    def resume_pollin(self):
        """Put :attr:`in_sock` back to the poller """
        self.poller.register(self.in_sock)

    @staticmethod
    def get_ctrl_address(
        host: Optional[str], port_ctrl: Optional[str], ctrl_with_ipc: bool
    ) -> Tuple[str, bool]:
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
        elif socks.get(self.out_sock, None) == zmq.POLLIN:
            return self.out_sock  # for dealer return idle status to router
        elif socks.get(self.in_sock) == zmq.POLLIN:
            return self.in_sock
        elif socks.get(self.in_connect_sock) == zmq.POLLIN:
            return self.in_connect_sock

    def _close_sockets(self):
        """Close input, output and control sockets of this `Zmqlet`. """
        for k in self.opened_socks:
            k.close()

    def _init_sockets(self) -> Tuple:
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
                ctrl_sock, ctrl_addr = _init_socket(
                    ctx,
                    self.ctrl_addr,
                    None,
                    SocketType.PAIR_BIND,
                    use_ipc=self.ctrl_with_ipc,
                )
            else:
                ctrl_sock, ctrl_addr = _init_socket(
                    ctx, __default_host__, self.args.port_ctrl, SocketType.PAIR_BIND
                )
            self.logger.debug(f'control over {colored(ctrl_addr, "yellow")}')

            in_sock, in_addr = _init_socket(
                ctx,
                self.args.host_in,
                self.args.port_in,
                self.args.socket_in,
                self.identity,
                ssh_server=self.args.ssh_server,
                ssh_keyfile=self.args.ssh_keyfile,
                ssh_password=self.args.ssh_password,
            )
            self.logger.debug(
                f'input {self.args.host_in}:{colored(self.args.port_in, "yellow")}'
            )
            out_sock, out_addr = _init_socket(
                ctx,
                self.args.host_out,
                self.args.port_out,
                self.args.socket_out,
                self.identity,
                ssh_server=self.args.ssh_server,
                ssh_keyfile=self.args.ssh_keyfile,
                ssh_password=self.args.ssh_password,
            )

            in_connect = None
            if self.args.hosts_in_connect:
                for address in self.args.hosts_in_connect:
                    if in_connect is None:
                        host, port = address.split(':')

                        in_connect, _ = _init_socket(
                            ctx,
                            host,
                            port,
                            SocketType.ROUTER_CONNECT,
                            self.identity,
                            ssh_server=self.args.ssh_server,
                            ssh_keyfile=self.args.ssh_keyfile,
                            ssh_password=self.args.ssh_password,
                        )
                    else:
                        _connect_socket(
                            in_connect,
                            address,
                            ssh_server=self.args.ssh_server,
                            ssh_keyfile=self.args.ssh_keyfile,
                            ssh_password=self.args.ssh_password,
                        )

            self.logger.debug(
                f'input {colored(in_addr, "yellow")} ({self.args.socket_in.name}) '
                f'output {colored(out_addr, "yellow")} ({self.args.socket_out.name}) '
                f'control over {colored(ctrl_addr, "yellow")} ({SocketType.PAIR_BIND.name})'
            )

            return ctx, in_sock, out_sock, ctrl_sock, in_connect
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

    def close(self, *args, **kwargs):
        """Close all sockets and shutdown the ZMQ context associated to this `Zmqlet`.

        .. note::
            This method is idempotent.

        :param args: Extra positional arguments
        :param kwargs: Extra key-value arguments
        """
        self._active = (
            False  # Important to avoid sending idle back while flushing in socket
        )
        if not self.is_closed:
            self.is_closed = True
            self._close_sockets()
            if hasattr(self, 'ctx'):
                self.ctx.term()
            self.print_stats()

    def print_stats(self):
        """Print out the network stats of of itself """
        self.logger.debug(
            f'#sent: {self.msg_sent} '
            f'#recv: {self.msg_recv} '
            f'sent_size: {get_readable_size(self.bytes_sent)} '
            f'recv_size: {get_readable_size(self.bytes_recv)}'
        )

    def _init_dynamic_out_socket(self, host_out, port_out):
        out_sock, _ = _init_socket(
            self.ctx,
            host_out,
            port_out,
            SocketType.DEALER_CONNECT,
            self.identity,
            ssh_server=self.args.ssh_server,
            ssh_keyfile=self.args.ssh_keyfile,
            ssh_password=self.args.ssh_password,
        )
        self.logger.debug(f'output {host_out}:{colored(port_out, "yellow")}')
        return out_sock

    def _get_dynamic_out_socket(self, target_pod, as_streaming=False):
        host = get_connect_host(target_pod.host, False, self.args)
        out_sock = self._init_dynamic_out_socket(host, target_pod.port)

        if as_streaming:
            out_sock = ZMQStream(out_sock, self.io_loop)

        self.opened_socks.append(out_sock)
        self.out_sockets[target_pod.full_address] = out_sock
        return out_sock

    def _get_dynamic_next_routes(self, message):
        routing_table = RoutingTable(message.envelope.routing_table)
        next_targets = routing_table.get_next_targets()
        next_routes = []
        for target, send_as_bind in next_targets:
            pod_address = target.active_target_pod.full_address

            if send_as_bind:
                out_socket = self.out_sock
            else:
                out_socket = self.out_sockets.get(pod_address, None)
                if out_socket is None:
                    out_socket = self._get_dynamic_out_socket(target.active_target_pod)

            next_routes.append((target, out_socket))
        return next_routes

    def _send_message_dynamic(self, msg: 'Message'):
        next_routes = self._get_dynamic_next_routes(msg)
        for routing_table, out_sock in next_routes:
            new_envelope = jina_pb2.EnvelopeProto()
            new_envelope.CopyFrom(msg.envelope)
            new_envelope.routing_table.CopyFrom(routing_table.proto)
            new_message = Message(request=msg.request, envelope=new_envelope)

            new_message.envelope.receiver_id = (
                routing_table.active_target_pod.target_identity
            )

            self._send_message_via(out_sock, new_message)

    def send_message(self, msg: 'Message'):
        """Send a message via the output socket

        :param msg: the protobuf message to send
        """
        # choose output sock
        if msg.is_data_request:
            if self.args.dynamic_routing_out:
                self._send_message_dynamic(msg)
                return
            out_sock = self.out_sock
        else:
            out_sock = self.ctrl_sock

        self._send_message_via(out_sock, msg)

    def _send_message_via(self, socket, msg):
        self.bytes_sent += send_message(socket, msg, **self.send_recv_kwargs)
        self.msg_sent += 1

        if self._active and socket == self.out_sock and self.in_sock_type == zmq.DEALER:
            self._send_idle_to_router()

    def _send_control_to_router(self, command, raise_exception=False):
        msg = ControlMessage(command, pod_name=self.name, identity=self.identity)
        self.bytes_sent += send_message(
            self.in_sock, msg, raise_exception=raise_exception, **self.send_recv_kwargs
        )
        self.msg_sent += 1
        self.logger.debug(
            f'control message {command} with id {self.identity} is sent to the router'
        )

    def _send_idle_to_router(self):
        """Tell the upstream router this dealer is idle """
        self._send_control_to_router('IDLE')

    def _send_cancel_to_router(self, raise_exception=False):
        """
        Tell the upstream router this dealer is canceled

        :param raise_exception: if true: raise an exception which might occur during send, if false: log error
        """
        self._active = False
        self._send_control_to_router('CANCEL', raise_exception)

    def recv_message(
        self, callback: Optional[Callable[['Message'], 'Message']] = None
    ) -> 'Message':
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
            else:
                return msg


class AsyncZmqlet(Zmqlet):
    """An async vesion of :class:`Zmqlet`.
    The :func:`send_message` and :func:`recv_message` works in the async manner.
    """

    def _get_zmq_ctx(self):
        return zmq.asyncio.Context()

    async def send_message(self, msg: 'Message', **kwargs):
        """Send a protobuf message in async via the output socket

        :param msg: the protobuf message to send
        :param kwargs: keyword arguments
        """
        if self.args.dynamic_routing_out:
            asyncio.create_task(self._send_message_dynamic(msg))
        else:
            asyncio.create_task(self._send_message_via(self.out_sock, msg))

    async def _send_message_dynamic(self, msg: 'Message'):
        for routing_table, out_sock in self._get_dynamic_next_routes(msg):
            new_envelope = jina_pb2.EnvelopeProto()
            new_envelope.CopyFrom(msg.envelope)
            new_envelope.routing_table.CopyFrom(routing_table.proto)
            new_message = Message(request=msg.request, envelope=new_envelope)
            asyncio.create_task(self._send_message_via(out_sock, new_message))

    async def _send_message_via(self, socket, msg):
        try:
            num_bytes = await send_message_async(socket, msg, **self.send_recv_kwargs)
            self.bytes_sent += num_bytes
            self.msg_sent += 1
        except (asyncio.CancelledError, TypeError) as ex:
            self.logger.error(f'sending message error: {ex!r}, gateway cancelled?')

    async def recv_message(
        self,
        callback: Optional[Callable[['Message'], Union['Message', 'Request']]] = None,
    ) -> Optional['Message']:
        """
        Receive a protobuf message in async manner.

        :param callback: Callback function to receive message
        :return: Received protobuf message. Or None in case of any error.
        """
        try:
            msg = await recv_message_async(self.in_sock, **self.send_recv_kwargs)
            self.msg_recv += 1
            if msg is not None:
                self.bytes_recv += msg.size
                if callback:
                    return callback(msg)
                else:
                    return msg
            else:
                self.logger.debug('Received message is empty.')
        except (asyncio.CancelledError, TypeError) as ex:
            self.logger.error(f'receiving message error: {ex!r}, gateway cancelled?')

    def __enter__(self):
        return self


class ZmqStreamlet(Zmqlet):
    """A :class:`ZmqStreamlet` object can send/receive data to/from ZeroMQ stream and invoke callback function. It
    has three sockets for input, output and control.

    .. warning::
        Starting from v0.3.6, :class:`ZmqStreamlet` replaces :class:`Zmqlet` as one of the key components in :class:`jina.peapods.runtime.BasePea`.
        It requires :mod:`tornado` and :mod:`uvloop` to be installed.
    """

    def __init__(
        self,
        ready_event: Union['multiprocessing.Event', 'threading.Event'],
        *args,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.is_ready_event = ready_event

    def _register_pollin(self):
        """Register :attr:`in_sock`, :attr:`ctrl_sock` and :attr:`out_sock` in poller."""
        with ImportExtensions(required=True):
            import tornado.ioloop

            get_or_reuse_loop()
            self.io_loop = tornado.ioloop.IOLoop.current()
        self.io_loop.add_callback(callback=lambda: self.is_ready_event.set())
        self.in_sock = ZMQStream(self.in_sock, self.io_loop)
        self.out_sock = ZMQStream(self.out_sock, self.io_loop)
        self.ctrl_sock = ZMQStream(self.ctrl_sock, self.io_loop)
        if self.in_connect_sock is not None:
            self.in_connect_sock = ZMQStream(self.in_connect_sock, self.io_loop)
        self.in_sock.stop_on_recv()

    def _get_dynamic_out_socket(self, target_pod):
        return super()._get_dynamic_out_socket(target_pod, as_streaming=True)

    def close(self, flush: bool = True, *args, **kwargs):
        """Close all sockets and shutdown the ZMQ context associated to this `Zmqlet`.

        .. note::
            This method is idempotent.

        :param flush: flag indicating if `sockets` need to be flushed before close is done
        :param args: Extra positional arguments
        :param kwargs: Extra key-value arguments
        """

        # if Address already in use `self.in_sock_type` is not set
        if (
            not self.is_closed
            and hasattr(self, 'in_sock_type')
            and self.in_sock_type == zmq.DEALER
        ):
            try:
                if self._active:
                    self._send_cancel_to_router(raise_exception=True)
            except zmq.error.ZMQError:
                self.logger.debug(
                    f'The dealer {self.name} can not unsubscribe from the router. '
                    f'In case the router is down this is expected.'
                )
        self._active = (
            False  # Important to avoid sending idle back while flushing in socket
        )
        if not self.is_closed:
            # wait until the close signal is received
            time.sleep(0.01)
            if flush:
                for s in self.opened_socks:
                    events = s.flush()
                    self.logger.debug(f'Handled #{events} during flush of socket')
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
                    if hasattr(self.in_connect_sock, '_handle_events'):
                        self.in_connect_sock._handle_events = (
                            lambda *args, **kwargs: None
                        )
                except AttributeError as e:
                    self.logger.error(f'failed to stop. {e!r}')

    def pause_pollin(self):
        """Remove :attr:`in_sock` from the poller """
        self.in_sock.stop_on_recv()
        self.is_polling_paused = True

    def resume_pollin(self):
        """Put :attr:`in_sock` back to the poller """
        if self.is_polling_paused:
            self.in_sock.on_recv(self._in_sock_callback)
            self.is_polling_paused = False

    def start(self, callback: Callable[['Message'], 'Message']):
        """
        Open all sockets and start the ZMQ context associated to this `Zmqlet`.

        :param callback: callback function to receive the protobuf message
        """

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
        if self.out_sock_type == zmq.ROUTER and not self.args.dynamic_routing_out:
            self.out_sock.on_recv(lambda x: _callback(x, self.out_sock_type))
        if self.in_connect_sock is not None:
            self.in_connect_sock.on_recv(
                lambda x: _callback(x, SocketType.ROUTER_CONNECT)
            )
        self.io_loop.start()
        self.io_loop.clear_current()
        self.io_loop.close(all_fds=True)


def send_ctrl_message(
    address: str, cmd: Union[str, Message], timeout: int, raise_exception: bool = False
) -> 'Message':
    """Send a control message to a specific address and wait for the response

    :param address: the socket address to send
    :param cmd: the control command to send
    :param timeout: the waiting time (in ms) for the response
    :param raise_exception: raise exception when exception found
    :return: received message
    """
    if isinstance(cmd, str):
        # we assume ControlMessage as default
        msg = ControlMessage(cmd)
    else:
        msg = cmd

    # control message is short, set a timeout and ask for quick response
    with zmq.Context() as ctx:
        ctx.setsockopt(zmq.LINGER, 0)
        sock, _ = _init_socket(ctx, address, None, SocketType.PAIR_CONNECT)
        send_message(sock, msg, raise_exception=raise_exception, timeout=timeout)
        r = None
        try:
            r = recv_message(sock, timeout)
        except Exception as ex:
            if raise_exception:
                raise ex
            else:
                pass
        finally:
            sock.close()
        return r


def send_message(
    sock: Union['zmq.Socket', 'ZMQStream'],
    msg: 'Message',
    raise_exception: bool = False,
    timeout: int = -1,
    **kwargs,
) -> int:
    """Send a protobuf message to a socket

    :param sock: the target socket to send
    :param msg: the protobuf message
    :param raise_exception: if true: raise an exception which might occur during send, if false: log error
    :param timeout: waiting time (in seconds) for sending
    :param kwargs: keyword arguments
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
            'is the server still online? is the network broken? are "port" correct?'
        )
    except zmq.error.ZMQError as ex:
        if raise_exception:
            raise ex
        else:
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


async def send_message_async(
    sock: 'zmq.Socket', msg: 'Message', timeout: int = -1, **kwargs
) -> int:
    """Send a protobuf message to a socket in async manner

    :param sock: the target socket to send
    :param msg: the protobuf message
    :param timeout: waiting time (in seconds) for sending
    :param kwargs: keyword arguments
    :return: the size (in bytes) of the sent message
    """
    try:
        _prep_send_socket(sock, timeout)
        await sock.send_multipart(msg.dump())
        return msg.size
    except zmq.error.Again:
        raise TimeoutError(
            f'cannot send message to sock {sock} after timeout={timeout}ms, please check the following:'
            'is the server still online? is the network broken? are "port" correct? '
        )
    except zmq.error.ZMQError as ex:
        default_logger.critical(ex)
    except asyncio.CancelledError:
        default_logger.debug('all gateway tasks are cancelled')
    except Exception as ex:
        raise ex
    finally:
        try:
            sock.setsockopt(zmq.SNDTIMEO, -1)
        except zmq.error.ZMQError:
            pass


def recv_message(sock: 'zmq.Socket', timeout: int = -1, **kwargs) -> 'Message':
    """Receive a protobuf message from a socket

    :param sock: the socket to pull from
    :param timeout: max wait time for pulling, -1 means wait forever
    :param kwargs: keyword arguments
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
            'is the server still online? is the network broken? are "port" correct? '
        )
    except Exception as ex:
        raise ex
    finally:
        sock.setsockopt(zmq.RCVTIMEO, -1)


async def recv_message_async(
    sock: 'zmq.Socket', timeout: int = -1, **kwargs
) -> 'Message':
    """Receive a protobuf message from a socket in async manner

    :param sock: the socket to pull from
    :param timeout: max wait time for pulling, -1 means wait forever
    :param kwargs: keyword arguments
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
            'is the server still online? is the network broken? are "port" correct? '
        )
    except zmq.error.ZMQError as ex:
        default_logger.critical(ex)
    except asyncio.CancelledError:
        default_logger.debug('all gateway tasks are cancelled')
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
        if len(frames) == 4:
            frames.pop(0)

    return Message(frames[1], frames[2])


def _get_random_ipc() -> str:
    """
    Get a random IPC address for control port

    :return: random IPC address
    """
    tmp = tempfile.NamedTemporaryFile().name

    return f'ipc://{tmp}'


def _init_socket(
    ctx: 'zmq.Context',
    host: str,
    port: Optional[int],
    socket_type: 'SocketType',
    identity: Optional[str] = None,
    use_ipc: bool = False,
    ssh_server: Optional[str] = None,
    ssh_keyfile: Optional[str] = None,
    ssh_password: Optional[str] = None,
) -> Tuple['zmq.Socket', str]:
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
        SocketType.ROUTER_CONNECT: lambda: ctx.socket(zmq.ROUTER),
    }[socket_type]()

    sock.setsockopt(zmq.LINGER, 0)

    if identity is not None:
        sock.set_string(zmq.IDENTITY, identity)

    if socket_type.is_bind:
        if use_ipc:
            sock.bind(host)
        else:
            # JEP2, if it is bind, then always bind to local
            if host != __default_host__:
                default_logger.warning(
                    f'host is set from {host} to {__default_host__} as the socket is in BIND type'
                )
                host = __default_host__
            if port is None:
                sock.bind_to_random_port(f'tcp://{host}')
            else:
                try:
                    sock.bind(f'tcp://{host}:{port}')
                except zmq.error.ZMQError:
                    default_logger.error(
                        f'error when binding port {port} to {host}, this port is occupied. '
                        f'If you are using Linux, try `lsof -i :{port}` to see which process '
                        f'occupies the port.'
                    )
                    raise
    else:
        if port is None:
            address = host
        else:
            address = f'tcp://{host}:{port}'

        # note that ssh only takes effect on CONNECT, not BIND
        # that means control socket setup does not need ssh
        _connect_socket(sock, address, ssh_server, ssh_keyfile, ssh_password)

    if socket_type in {SocketType.SUB_CONNECT, SocketType.SUB_BIND}:
        # sock.setsockopt(zmq.SUBSCRIBE, identity.encode('ascii') if identity else b'')
        sock.subscribe('')  # An empty shall subscribe to all incoming messages

    return sock, sock.getsockopt_string(zmq.LAST_ENDPOINT)


def _connect_socket(
    sock,
    address,
    ssh_server: Optional[str] = None,
    ssh_keyfile: Optional[str] = None,
    ssh_password: Optional[str] = None,
):
    if ssh_server is not None:
        tunnel_connection(sock, address, ssh_server, ssh_keyfile, ssh_password)
    else:
        sock.connect(address)
