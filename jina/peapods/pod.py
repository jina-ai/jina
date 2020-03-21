import argparse
import copy
from contextlib import ExitStack
from queue import Empty
from typing import Set, Dict, List, Callable, Union

from . import Pea
from .gateway import GatewayPea
from .pea import BasePea
from .. import __default_host__
from ..enums import *
from ..helper import random_port, random_identity, kwargs2list
from ..main.parser import set_pod_parser, set_gateway_parser


class BasePod:
    """A BasePod is a immutable set of peas, which run in parallel. They share the same input and output socket.
    Internally, the peas can run with the process/thread backend. They can be also run in their own containers
    """

    def __init__(self, args: Union['argparse.Namespace', Dict]):
        """

        :param args: arguments parsed from the CLI
        """
        self.peas = []
        self.is_head_router = False
        self.is_tail_router = False
        self.deducted_head = None
        self.deducted_tail = None
        self.peas_args = self._parse_args(args)

    @property
    def name(self) -> str:
        """The name of this :class:`BasePod`. """
        return self.peas_args['peas'][0].name

    @property
    def port_grpc(self) -> int:
        """Get the grpc port number """
        return self.peas_args['peas'][0].port_grpc

    @property
    def host(self) -> str:
        """Get the grpc host name """
        return self.peas_args['peas'][0].host

    def _parse_args(self, args):
        peas_args = {
            'head': None,
            'tail': None,
            'peas': []
        }

        if getattr(args, 'replicas', 1) > 1:
            # reasons to separate head and tail from peas is that they
            # can be deducted based on the previous and next pods
            peas_args['head'] = _copy_to_head_args(args, args.replica_type.is_push)
            peas_args['tail'] = _copy_to_tail_args(args,
                                                   args.num_part if args.replica_type.is_block else 1)
            peas_args['peas'] = _set_peas_args(args, peas_args['head'], peas_args['tail'])
            self.is_head_router = True
            self.is_tail_router = True
        else:
            peas_args['peas'] = [args]

        # note that peas_args['peas'][0] exist either way and carries the original property
        return peas_args

    @property
    def head_args(self):
        """Get the arguments for the `head` of this BasePod. """
        if self.is_head_router and self.peas_args['head']:
            return self.peas_args['head']
        elif not self.is_head_router and len(self.peas_args['peas']) == 1:
            return self.peas_args['peas'][0]
        elif self.deducted_head:
            return self.deducted_head
        else:
            raise ValueError('ambiguous head node, maybe it is deducted already?')

    @head_args.setter
    def head_args(self, args):
        """Set the arguments for the `head` of this BasePod. """
        if self.is_head_router and self.peas_args['head']:
            self.peas_args['head'] = args
        elif not self.is_head_router and len(self.peas_args['peas']) == 1:
            self.peas_args['peas'][0] = args
        elif self.deducted_head:
            self.deducted_head = args
        else:
            raise ValueError('ambiguous head node, maybe it is deducted already?')

    @property
    def tail_args(self):
        """Get the arguments for the `tail` of this BasePod. """
        if self.is_tail_router and self.peas_args['tail']:
            return self.peas_args['tail']
        elif not self.is_tail_router and len(self.peas_args['peas']) == 1:
            return self.peas_args['peas'][0]
        elif self.deducted_tail:
            return self.deducted_tail
        else:
            raise ValueError('ambiguous tail node, maybe it is deducted already?')

    @tail_args.setter
    def tail_args(self, args):
        """Get the arguments for the `tail` of this BasePod. """
        if self.is_tail_router and self.peas_args['tail']:
            self.peas_args['tail'] = args
        elif not self.is_tail_router and len(self.peas_args['peas']) == 1:
            self.peas_args['peas'][0] = args
        elif self.deducted_tail:
            self.deducted_tail = args
        else:
            raise ValueError('ambiguous tail node, maybe it is deducted already?')

    @property
    def all_args(self):
        """Get all arguments of all Peas in this BasePod. """
        return self.peas_args['peas'] + (
            [self.peas_args['head']] if self.peas_args['head'] else []) + (
                   [self.peas_args['tail']] if self.peas_args['tail'] else [])

    @property
    def num_peas(self) -> int:
        """Get the number of running :class:`BasePea`"""
        return len(self.peas)

    def __eq__(self, other: 'BasePod'):
        return self.num_peas == other.num_peas and self.name == other.name

    def set_runtime(self, runtime: str):
        """Set the parallel runtime of this BasePod.

        :param runtime: possible values: process, thread
        """
        for s in self.all_args:
            s.runtime = runtime
            # for thread and process backend which runs locally, host_in and host_out should not be set
            # s.host_in = __default_host__
            # s.host_out = __default_host__

    def start(self):
        """Start to run all Peas in this BasePod.

        Remember to close the BasePod with :meth:`close`.

        Note that this method has a timeout of ``timeout_ready`` set in CLI,
        which is inherited from :class:`jina.peapods.peas.BasePea`
        """
        self.stack = ExitStack()
        # start head and tail
        if self.peas_args['head']:
            p = BasePea(self.peas_args['head'])
            self.peas.append(p)
            self.stack.enter_context(p)

        if self.peas_args['tail']:
            p = BasePea(self.peas_args['tail'])
            self.peas.append(p)
            self.stack.enter_context(p)

        # start real peas and accumulate the storage id
        for idx, s in enumerate(self.peas_args['peas']):
            s.replica_id = idx
            p = Pea(s, allow_remote=False)
            self.peas.append(p)
            self.stack.enter_context(p)

    @property
    def log_iterator(self):
        """Get the last log using iterator

        The :class:`BasePod` log iterator goes through all peas :attr:`log_iterator` and
        poll them sequentially. If non all them is active anymore, aka :attr:`is_event_loop`
        is False, then the iterator ends.

        .. warning::

            The log may not strictly follow the time order given that we are polling the log
            from all peas in the sequential manner.
        """
        from ..logging.queue import __log_queue__
        while not self.is_shutdown:
            try:
                yield __log_queue__.get_nowait()
            except Empty:
                pass

    @property
    def is_shutdown(self) -> bool:
        return all(p.is_shutdown.is_set() for p in self.peas)

    def __enter__(self):
        self.start()
        return self

    @property
    def status(self) -> List:
        """The status of a BasePod is the list of status of all its Peas """
        return [p.status for p in self.peas]

    def is_ready(self) -> bool:
        """Wait till the ready signal of this BasePod.

        The pod is ready only when all the contained Peas returns is_ready
        """
        for p in self.peas:
            p.is_ready.wait()
        return True

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def join(self):
        """Wait until all peas exit"""
        try:
            for s in self.peas:
                s.join()
        except KeyboardInterrupt:
            pass
        finally:
            self.peas.clear()

    def close(self):
        self.stack.close()


class ParsedPod(BasePod):
    """A :class:`ParsedPod` is a pod where all peas and their connections are given"""

    def _parse_args(self, args):
        return args


class FlowPod(BasePod):
    """A :class:`FlowPod` is like a :class:`BasePod`, but it exposes more interfaces for tweaking its connections with
    other Pods, which comes in handy when used in the Flow API """

    def __init__(self, kwargs: Dict, send_to: Set[str] = None,
                 recv_from: Set[str] = None, parser: Callable = set_pod_parser):
        """

        :param kwargs: unparsed argument in dict, if given the
        :param send_to: a list of names this BasePod send message to
        :param recv_from: a list of names this BasePod receive message from
        """
        self.cli_args, self._args, self.unk_args = _get_parsed_args(kwargs, parser)
        super().__init__(self._args)
        self.send_to = send_to if send_to else set()  #: used in the :class:`jina.flow.Flow` to build the graph
        self.recv_from = recv_from if recv_from else set()  #: used in the :class:`jina.flow.Flow` to build the graph

    def to_cli_command(self):
        if isinstance(self, GatewayPod):
            cmd = 'jina gateway'
        else:
            cmd = 'jina pod'

        return '%s %s' % (cmd, ' '.join(self.cli_args))

    @staticmethod
    def connect(first: 'BasePod', second: 'BasePod', first_socket_type: 'SocketType'):
        """Connect two Pods

        :param first: the first BasePod
        :param second: the second BasePod
        :param first_socket_type: socket type of the first BasePod, availables are PUSH_BIND, PUSH_CONNECT, PUB_BIND
        """
        if first_socket_type == SocketType.PUSH_BIND:
            first.tail_args.socket_out = SocketType.PUSH_BIND
            second.head_args.socket_in = SocketType.PULL_CONNECT

            first.tail_args.host_out = __default_host__
            second.head_args.host_in = _fill_in_host(bind_args=first.tail_args,
                                                     connect_args=second.head_args)
            second.head_args.port_in = first.tail_args.port_out
        elif first_socket_type == SocketType.PUSH_CONNECT:
            first.tail_args.socket_out = SocketType.PUSH_CONNECT
            second.head_args.socket_in = SocketType.PULL_BIND

            first.tail_args.host_out = _fill_in_host(connect_args=first.tail_args,
                                                     bind_args=second.head_args)
            second.head_args.host_in = __default_host__
            first.tail_args.port_out = second.head_args.port_in
        elif first_socket_type == SocketType.PUB_BIND:
            first.tail_args.socket_out = SocketType.PUB_BIND
            second.head_args.socket_in = SocketType.SUB_CONNECT

            first.tail_args.host_out = __default_host__  # bind always get default 0.0.0.0
            second.head_args.host_in = _fill_in_host(bind_args=first.tail_args,
                                                     connect_args=second.head_args)  # the hostname of s_pod
            second.head_args.port_in = first.tail_args.port_out
        else:
            raise NotImplementedError('%r is not supported here' % first_socket_type)

    def connect_to_tail_of(self, pod: 'BasePod'):
        """Eliminate the head node by connecting prev_args node directly to peas """
        if self._args.replicas > 1 and self.is_head_router:
            # keep the port_in and socket_in of prev_args
            # only reset its output
            pod.tail_args = _copy_to_head_args(pod.tail_args, self._args.replica_type.is_push, as_router=False)
            # update peas to receive from it
            self.peas_args['peas'] = _set_peas_args(self._args, pod.tail_args, self.tail_args)
            # remove the head node
            self.peas_args['head'] = None
            # head is no longer a router anymore
            self.is_head_router = False
            self.deducted_head = pod.tail_args
        else:
            raise ValueError('the current pod has no head router, deduct the head is confusing')

    def connect_to_head_of(self, pod: 'BasePod'):
        """Eliminate the tail node by connecting next_args node directly to peas """
        if self._args.replicas > 1 and self.is_tail_router:
            # keep the port_out and socket_out of next_arts
            # only reset its input
            pod.head_args = _copy_to_tail_args(pod.head_args,
                                               self._args.num_part if self._args.replica_type.is_block else 1,
                                               as_router=False)
            # update peas to receive from it
            self.peas_args['peas'] = _set_peas_args(self._args, self.head_args, pod.head_args)
            # remove the head node
            self.peas_args['tail'] = None
            # head is no longer a router anymore
            self.is_tail_router = False
            self.deducted_tail = pod.head_args
        else:
            raise ValueError('the current pod has no tail router, deduct the tail is confusing')

    def start(self):
        if self._args.host == __default_host__:
            return super().start()
        else:
            from .remote import RemoteParsedPod
            print(self.peas_args)
            _remote_pod = RemoteParsedPod(self.peas_args)
            self.stack = ExitStack()
            self.stack.enter_context(_remote_pod)


def _set_peas_args(args, head_args, tail_args):
    result = []
    for _ in range(args.replicas):
        _args = copy.deepcopy(args)
        _args.port_in = head_args.port_out
        _args.port_out = tail_args.port_in
        _args.port_ctrl = random_port()
        _args.identity = random_identity()
        _args.socket_out = SocketType.PUSH_CONNECT
        if args.replica_type.is_push:
            _args.socket_in = SocketType.PULL_CONNECT
        else:
            _args.socket_in = SocketType.SUB_CONNECT
        _args.host_in = _fill_in_host(bind_args=head_args, connect_args=_args)
        _args.host_out = _fill_in_host(bind_args=tail_args, connect_args=_args)
        result.append(_args)
    return result


def _set_router_args(args):
    from pkg_resources import resource_filename
    args.yaml_path = resource_filename('jina', '/'.join(('resources', 'executors.route.yml')))
    args.name = 'router'


def _copy_to_head_args(args, is_push: bool, as_router: bool = True):
    """Set the outgoing args of the head router"""

    _head_args = copy.deepcopy(args)
    _head_args.port_ctrl = random_port()
    _head_args.port_out = random_port()
    if as_router:
        _set_router_args(_head_args)
    if is_push:
        _head_args.socket_out = SocketType.PUSH_BIND
    else:
        _head_args.socket_out = SocketType.PUB_BIND
    return _head_args


def _copy_to_tail_args(args, num_part: int, as_router: bool = True):
    """Set the incoming args of the tail router"""

    _tail_args = copy.deepcopy(args)
    _tail_args.port_in = random_port()
    _tail_args.port_ctrl = random_port()
    _tail_args.socket_in = SocketType.PULL_BIND
    if as_router:
        _set_router_args(_tail_args)
    _tail_args.num_part = num_part
    return _tail_args


def _get_parsed_args(kwargs, parser):
    args = kwargs2list(kwargs)
    try:
        p_args, unknown_args = parser().parse_known_args(args)
    except SystemExit:
        raise ValueError('bad arguments "%s" with parser %r, '
                         'you may want to double check your args ' % (args, parser))
    return args, p_args, unknown_args


def _fill_in_host(bind_args, connect_args):
    from sys import platform

    bind_local = (bind_args.host == '0.0.0.0')
    bind_docker = (bind_args.image is not None and bind_args.image)
    conn_local = (connect_args.host == '0.0.0.0')
    conn_docker = (connect_args.image is not None and connect_args.image)
    bind_conn_same_remote = not bind_local and not conn_local and (bind_args.host == connect_args.host)
    if platform == "linux" or platform == "linux2":
        local_host = '0.0.0.0'
    else:
        local_host = 'host.docker.internal'

    if bind_local and conn_local and conn_docker:
        return local_host
    elif bind_local and conn_local and not conn_docker:
        return __default_host__
    elif not bind_local and bind_conn_same_remote:
        if conn_docker:
            return local_host
        else:
            return __default_host__
    else:
        return bind_args.host


class GatewayPod(BasePod):
    """A :class:`BasePod` that holds a Gateway """

    def start(self):
        self.stack = ExitStack()
        for s in self.all_args:
            p = GatewayPea(s)
            self.peas.append(p)
            self.stack.enter_context(p)


class GatewayFlowPod(GatewayPod, FlowPod):
    """A :class:`FlowPod` that holds a Gateway """

    def __init__(self, kwargs: Dict = None):
        FlowPod.__init__(self, kwargs, parser=set_gateway_parser)
