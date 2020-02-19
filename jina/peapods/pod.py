import copy
from contextlib import ExitStack
from typing import Set, Dict, Callable

from .frontend import FrontendPea
from .pea import Pea
from .. import __default_host__
from ..enums import *
from ..helper import random_port, random_identity
from ..main.parser import set_pod_parser

if False:
    import argparse


class Pod:
    """A Pod is a set of peas, which run in parallel. They share the same input and output socket.
    Internally, the peas can run with the process/thread backend.
    """

    def __init__(self, args: 'argparse.Namespace' = None, kwargs: Dict = None, send_to: Set[str] = None,
                 recv_from: Set[str] = None, parser: Callable = set_pod_parser):
        """

        :param args: arguments parsed from the CLI, if given then ``kwargs`` is ignored
        :param name: the name of the Pod
        :param kwargs: unparsed argument in dict, if given the
        :param send_to: a list of names this Pod send message to
        :param recv_from: a list of names this Pod receive message from
        """
        self.peas = []

        if args:
            self._args = args
        else:
            self.cli_args, self._args, self.unk_args = _get_parsed_args(kwargs, parser)

        self.name = self._args.name
        self.send_to = send_to if send_to else set()
        self.recv_from = recv_from if recv_from else set()

        self.is_head_router = False
        self.is_tail_router = False
        self.deducted_head = None
        self.deducted_tail = None
        self.peas_args = self._parse_args()

    def __eq__(self, other):
        return all(getattr(self, v) == getattr(other, v) for v in ('name', 'send_to', 'recv_from'))

    def to_cli_command(self):
        if isinstance(self, FrontendPod):
            cmd = 'jina frontend'
        else:
            cmd = 'jina pod'

        return '%s %s' % (cmd, ' '.join(self.cli_args))

    def _parse_args(self):
        peas_args = {
            'head': None,
            'tail': None,
            'peas': []
        }

        if self._args.num_parallel > 1:
            # reasons to separate head and tail from peas is that they
            # can be deducted based on the previous and next pods
            peas_args['head'] = _copy_to_head_args(self._args, self._args.parallel_type.is_push)
            peas_args['tail'] = _copy_to_tail_args(self._args,
                                                   self._args.num_part if self._args.parallel_type.is_block else 1)
            peas_args['peas'] = _set_peas_args(self._args, peas_args['head'], peas_args['tail'])
            self.is_head_router = True
            self.is_tail_router = True
        else:
            peas_args['peas'] = [self._args]
        return peas_args

    @property
    def head_args(self):
        """Get the arguments for the `head` of this Pod. """
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
        """Set the arguments for the `head` of this Pod. """
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
        """Get the arguments for the `tail` of this Pod. """
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
        """Get the arguments for the `tail` of this Pod. """
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
        """Get all arguments of all Peas in this Pod. """
        return self.peas_args['peas'] + (
            [self.peas_args['head']] if self.peas_args['head'] else []) + (
                   [self.peas_args['tail']] if self.peas_args['tail'] else [])

    @property
    def num_peas(self) -> int:
        """Get the number of running :class:`Pea`"""
        return len(self.peas)

    def set_parallel_runtime(self, runtime: str):
        """Set the parallel runtime of this Pod.

        :param runtime: possible values: process, thread
        """
        for s in self.all_args:
            s.parallel_runtime = runtime
            # for thread and process backend which runs locally, host_in and host_out should not be set
            s.host_in = __default_host__
            s.host_out = __default_host__

    def __enter__(self):
        self.stack = ExitStack()
        # start head and tail
        if self.peas_args['head']:
            p = Pea(self.peas_args['head'])
            self.peas.append(p)
            self.stack.enter_context(p)

        if self.peas_args['tail']:
            p = Pea(self.peas_args['tail'])
            self.peas.append(p)
            self.stack.enter_context(p)

        # start real peas and accumulate the storage id
        for idx, s in enumerate(self.peas_args['peas']):
            p = Pea(s, replica_id=idx)
            self.peas.append(p)
            self.stack.enter_context(p)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stack.close()

    def join(self):
        """Wait until all peas exit"""
        try:
            for s in self.peas:
                s.join()
        except KeyboardInterrupt:
            pass
        finally:
            self.peas.clear()

    def connect_to_last(self, pod: 'Pod'):
        """Eliminate the head node by connecting prev_args node directly to peas """
        if self._args.num_parallel > 1 and self.is_head_router:
            # keep the port_in and socket_in of prev_args
            # only reset its output
            pod.tail_args = _copy_to_head_args(pod.tail_args, self._args.parallel_type.is_push, as_router=False)
            # update peas to receive from it
            self.peas_args['peas'] = _set_peas_args(self._args, pod.tail_args, self.tail_args)
            # remove the head node
            self.peas_args['head'] = None
            # head is no longer a router anymore
            self.is_head_router = False
            self.deducted_head = pod.tail_args
        else:
            raise ValueError('the current pod has no head router, deduct the head is confusing')

    def connect_to_next(self, pod: 'Pod'):
        """Eliminate the tail node by connecting next_args node directly to peas """
        if self._args.num_parallel > 1 and self.is_tail_router:
            # keep the port_out and socket_out of next_arts
            # only reset its input
            pod.head_args = _copy_to_tail_args(pod.head_args,
                                               self._args.num_part if self._args.parallel_type.is_block else 1,
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

    @staticmethod
    def connect(first: 'Pod', second: 'Pod', bind_on_first: bool):
        """Connect two Pods

        :param first: the first Pod
        :param second: the second Pod
        :param bind_on_first: do socket binding on the first Pod
        """
        if bind_on_first:
            first.tail_args.socket_out = SocketType.PUSH_BIND
            second.head_args.socket_in = SocketType.PULL_CONNECT

            first.tail_args.host_out = __default_host__
            second.head_args.host_in = first.name
            second.head_args.port_in = first.tail_args.port_out
        else:
            first.tail_args.socket_out = SocketType.PUSH_CONNECT
            second.head_args.socket_in = SocketType.PULL_BIND

            first.tail_args.host_out = second.name
            second.head_args.host_in = __default_host__
            first.tail_args.port_out = second.head_args.port_in


def _set_peas_args(args, head_args, tail_args):
    result = []
    for _ in range(args.num_parallel):
        _args = copy.deepcopy(args)
        _args.port_in = head_args.port_out
        _args.port_out = tail_args.port_in
        _args.port_ctrl = random_port()
        _args.identity = random_identity()
        _args.socket_out = SocketType.PUSH_CONNECT
        if args.parallel_type.is_push:
            _args.socket_in = SocketType.PULL_CONNECT
        else:
            _args.socket_in = SocketType.SUB_CONNECT
        result.append(_args)
    return result


def _set_router_args(args):
    args.exec_yaml_path = None
    args.driver_group = 'route'
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
    args = []
    for k, v in kwargs.items():
        if isinstance(v, bool):
            if v:
                if not k.startswith('no_') and not k.startswith('no-'):
                    args.append('--%s' % k)
                else:
                    args.append('--%s' % k[3:])
            else:
                if k.startswith('no_') or k.startswith('no-'):
                    args.append('--%s' % k)
                else:
                    args.append('--no_%s' % k)
        elif isinstance(v, list):  # for nargs
            args.extend(['--%s' % k, *(str(vv) for vv in v)])
        else:
            args.extend(['--%s' % k, str(v)])
    try:
        p_args, unknown_args = parser().parse_known_args(args)
    except SystemExit:
        raise ValueError('bad arguments "%s" with parser %r, '
                         'you may want to double check your args ' % (args, parser))
    return args, p_args, unknown_args


class FrontendPod(Pod):
    """A Pod-like Frontend """

    def __enter__(self):
        self.stack = ExitStack()
        for s in self.all_args:
            p = FrontendPea(s)
            self.peas.append(p)
            self.stack.enter_context(p)
        return self

    @property
    def grpc_port(self) -> int:
        """Get the grpc port number """
        return self._args.grpc_port

    @property
    def grpc_host(self) -> str:
        """Get the grpc host name """
        return self._args.grpc_host
