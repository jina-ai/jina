__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
import copy
import time
from contextlib import ExitStack
from queue import Empty
from threading import Thread
from typing import Set, Dict, List, Callable, Union

from . import Pea
from .gateway import GatewayPea, RESTGatewayPea
from .pea import BasePea
from .. import __default_host__
from ..enums import *
from ..helper import random_port, get_random_identity, get_parsed_args, get_non_defaults_args
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
        if hasattr(args, 'polling') and args.polling.is_push:
            # ONLY reset when it is push
            args.reducing_yaml_path = '_forward'
        self._args = args
        self.peas_args = self._parse_args(args)

    @property
    def is_idle(self) -> bool:
        """A Pod is idle when all its peas are idle, see also :attr:`jina.peapods.pea.Pea.is_idle`.
        """
        return all(p.is_idle for p in self.peas if p.is_ready.is_set())

    def close_if_idle(self):
        """Check every second if the pod is in idle, if yes, then close the pod"""
        while True:
            if self.is_idle:
                self.close()
                break  # only run once
            time.sleep(1)

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
            peas_args['head'] = _copy_to_head_args(args, args.polling.is_push)
            peas_args['tail'] = _copy_to_tail_args(args)
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

    def start_sentinels(self):
        self.sentinel_threads = []
        if isinstance(self._args, argparse.Namespace) and getattr(self._args, 'shutdown_idle', False):
            self.sentinel_threads.append(Thread(target=self.close_if_idle,
                                                name='sentinel-shutdown-idle',
                                                daemon=True))
        for t in self.sentinel_threads:
            t.start()

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
        if len(self.peas_args['peas']) > 1:
            start_rep_id = 1
        else:
            start_rep_id = 0
        for idx, _args in enumerate(self.peas_args['peas'], start=start_rep_id):
            _args.replica_id = idx
            _args.role = PeaRoleType.REPLICA
            p = Pea(_args, allow_remote=False)
            self.peas.append(p)
            self.stack.enter_context(p)

        self.start_sentinels()
        return self

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
        return all(not p.is_ready.is_set() for p in self.peas)

    def __enter__(self):
        return self.start()

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


class MutablePod(BasePod):
    """A :class:`MutablePod` is a pod where all peas and their connections are given"""

    def _parse_args(self, args):
        return args


class FlowPod(BasePod):
    """A :class:`FlowPod` is like a :class:`BasePod`, but it exposes more interfaces for tweaking its connections with
    other Pods, which comes in handy when used in the Flow API
    """

    def __init__(self, kwargs: Dict,
                 needs: Set[str] = None, parser: Callable = set_pod_parser):
        """

        :param kwargs: unparsed argument in dict, if given the
        :param needs: a list of names this BasePod needs to receive message from
        """
        _parser = parser()
        self.cli_args, self._args, self.unk_args = get_parsed_args(kwargs, _parser, 'FlowPod')
        super().__init__(self._args)
        self.needs = needs if needs else set()  #: used in the :class:`jina.flow.Flow` to build the graph
        self._kwargs = get_non_defaults_args(self._args, _parser)

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
            first.tail_args.num_part += 1
            first.tail_args.yaml_path = '- !!PublishDriver | {num_part: %d}' % first.tail_args.num_part
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
            pod.tail_args = _copy_to_head_args(pod.tail_args, self._args.polling.is_push, as_router=False)
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
            from .remote import RemoteMutablePod
            _remote_pod = RemoteMutablePod(self.peas_args)
            self.stack = ExitStack()
            self.stack.enter_context(_remote_pod)
            self.start_sentinels()
            return self


def _set_peas_args(args, head_args, tail_args):
    result = []
    for _ in range(args.replicas):
        _args = copy.deepcopy(args)
        _args.port_in = head_args.port_out
        _args.port_out = tail_args.port_in
        _args.port_ctrl = random_port()
        _args.identity = get_random_identity()
        _args.socket_out = SocketType.PUSH_CONNECT
        if args.polling.is_push:
            if args.scheduling == SchedulerType.ROUND_ROBIN:
                _args.socket_in = SocketType.PULL_CONNECT
            elif args.scheduling == SchedulerType.LOAD_BALANCE:
                _args.socket_in = SocketType.DEALER_CONNECT
            else:
                raise NotImplementedError
        else:
            _args.socket_in = SocketType.SUB_CONNECT
        _args.host_in = _fill_in_host(bind_args=head_args, connect_args=_args)
        _args.host_out = _fill_in_host(bind_args=tail_args, connect_args=_args)
        result.append(_args)
    return result


def _copy_to_head_args(args, is_push: bool, as_router: bool = True):
    """Set the outgoing args of the head router
    """

    _head_args = copy.deepcopy(args)
    _head_args.port_ctrl = random_port()
    _head_args.port_out = random_port()
    if is_push:
        if args.scheduling == SchedulerType.ROUND_ROBIN:
            _head_args.socket_out = SocketType.PUSH_BIND
            if as_router:
                _head_args.yaml_path = '_forward'
        elif args.scheduling == SchedulerType.LOAD_BALANCE:
            _head_args.socket_out = SocketType.ROUTER_BIND
            if as_router:
                _head_args.yaml_path = '_route'
    else:
        _head_args.socket_out = SocketType.PUB_BIND
        if as_router:
            _head_args.yaml_path = '- !!PublishDriver |  {num_part: %d}' % args.replicas

    if as_router:
        _head_args.name = args.name or ''
        _head_args.role = PeaRoleType.HEAD

    # head and tail never run in docker, reset their image to None
    _head_args.image = None
    return _head_args


def _copy_to_tail_args(args, as_router: bool = True):
    """Set the incoming args of the tail router
    """
    _tail_args = copy.deepcopy(args)
    _tail_args.port_in = random_port()
    _tail_args.port_ctrl = random_port()
    _tail_args.socket_in = SocketType.PULL_BIND
    if as_router:
        _tail_args.yaml_path = args.reducing_yaml_path
        _tail_args.name = args.name or ''
        _tail_args.role = PeaRoleType.TAIL

    # head and tail never run in docker, reset their image to None
    _tail_args.image = None
    return _tail_args


def _fill_in_host(bind_args, connect_args):
    from sys import platform

    bind_local = (bind_args.host == '0.0.0.0')
    bind_docker = (bind_args.image is not None and bind_args.image)
    conn_tail = (connect_args.name is not None and connect_args.role == PeaRoleType.TAIL)
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
            p = RESTGatewayPea(s) if getattr(s, 'rest_api', False) else GatewayPea(s)
            self.peas.append(p)
            self.stack.enter_context(p)

        self.start_sentinels()
        return self


class GatewayFlowPod(GatewayPod, FlowPod):
    """A :class:`FlowPod` that holds a Gateway """

    def __init__(self, kwargs: Dict = None, needs: Set[str] = None):
        FlowPod.__init__(self, kwargs, needs, parser=set_gateway_parser)
