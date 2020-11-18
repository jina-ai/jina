__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
import copy
import time
from argparse import Namespace
from contextlib import ExitStack
from threading import Thread
from typing import Optional, Set, Dict, List, Callable, Union

from . import Pea
from .gateway import GatewayPea, RESTGatewayPea
from .head_pea import HeadPea
from .tail_pea import TailPea
from .. import __default_host__
from ..enums import *
from ..helper import random_port, get_random_identity, get_parsed_args, get_non_defaults_args, \
    is_valid_local_config_source, get_internal_ip, get_public_ip
from ..parser import set_pod_parser, set_gateway_parser


class BasePod(ExitStack):
    """A BasePod is a immutable set of peas, which run in parallel. They share the same input and output socket.
    Internally, the peas can run with the process/thread backend. They can be also run in their own containers
    """

    def __init__(self, args: Union['argparse.Namespace', Dict]):
        """

        :param args: arguments parsed from the CLI
        """
        super().__init__()
        self.peas = []
        self.is_head_router = False
        self.is_tail_router = False
        self.deducted_head = None
        self.deducted_tail = None
        self._args = args
        self.peas_args = self._parse_args(args)

    @property
    def is_singleton(self) -> bool:
        """Return if the Pod contains only a single Pea """
        return not (self.is_head_router or self.is_tail_router)

    @property
    def is_idle(self) -> bool:
        """A Pod is idle when all its peas are idle, see also :attr:`jina.peapods.pea.Pea.is_idle`.
        """
        return all(p.is_idle for p in self.peas if p.is_ready_event.is_set())

    def close_if_idle(self):
        """Check every second if the pod is in idle, if yes, then close the pod"""
        while True:
            if self.is_idle:
                self.close()
            time.sleep(1)

    @property
    def name(self) -> str:
        """The name of this :class:`BasePod`. """
        return self.first_pea_args.name

    @property
    def port_expose(self) -> int:
        """Get the grpc port number """
        return self.first_pea_args.port_expose

    @property
    def host(self) -> str:
        """Get the host name of this Pod"""
        return self.first_pea_args.host

    @property
    def host_in(self) -> str:
        """Get the host_in of this pod"""
        return self.head_args.host_in

    @property
    def host_out(self) -> str:
        """Get the host_out of this pod"""
        return self.tail_args.host_out

    @property
    def address_in(self) -> str:
        """Get the full incoming address of this pod"""
        return f'{self.head_args.host_in}:{self.head_args.port_in} ({self.head_args.socket_in!s})'

    @property
    def address_out(self) -> str:
        """Get the full outgoing address of this pod"""
        return f'{self.tail_args.host_out}:{self.tail_args.port_out} ({self.head_args.socket_out!s})'

    @property
    def first_pea_args(self) -> Namespace:
        """Return the first non-head/tail pea's args """
        # note this will be never out of boundary
        return self.peas_args['peas'][0]

    def _parse_args(self, args: Namespace) -> Dict[str, Optional[Union[List[Namespace], Namespace]]]:
        peas_args = {
            'head': None,
            'tail': None,
            'peas': []
        }
        if getattr(args, 'parallel', 1) > 1:
            # reasons to separate head and tail from peas is that they
            # can be deducted based on the previous and next pods
            _set_after_to_pass(args)
            self.is_head_router = True
            self.is_tail_router = True
            peas_args['head'] = _copy_to_head_args(args, args.polling.is_push)
            peas_args['tail'] = _copy_to_tail_args(args)
            peas_args['peas'] = _set_peas_args(args, peas_args['head'], peas_args['tail'])
        elif getattr(args, 'uses_before', None) or getattr(args, 'uses_after', None):
            args.scheduling = SchedulerType.ROUND_ROBIN
            if getattr(args, 'uses_before', None):
                self.is_head_router = True
                peas_args['head'] = _copy_to_head_args(args, args.polling.is_push)
            if getattr(args, 'uses_after', None):
                self.is_tail_router = True
                peas_args['tail'] = _copy_to_tail_args(args)
            peas_args['peas'] = _set_peas_args(args, peas_args.get('head', None), peas_args.get('tail', None))
        else:
            _set_after_to_pass(args)
            self.is_head_router = False
            self.is_tail_router = False
            peas_args['peas'] = [args]

        # note that peas_args['peas'][0] exist either way and carries the original property
        return peas_args

    @property
    def head_args(self):
        """Get the arguments for the `head` of this BasePod. """
        if self.is_head_router and self.peas_args['head']:
            return self.peas_args['head']
        elif not self.is_head_router and len(self.peas_args['peas']) == 1:
            return self.first_pea_args
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
            self.peas_args['peas'][0] = args  # weak reference
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
            return self.first_pea_args
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
            self.peas_args['peas'][0] = args  # weak reference
        elif self.deducted_tail:
            self.deducted_tail = args
        else:
            raise ValueError('ambiguous tail node, maybe it is deducted already?')

    @property
    def all_args(self) -> List[Namespace]:
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

    def start_sentinels(self) -> None:
        self.sentinel_threads = []
        if isinstance(self._args, argparse.Namespace) and getattr(self._args, 'shutdown_idle', False):
            self.sentinel_threads.append(Thread(target=self.close_if_idle,
                                                name='sentinel-shutdown-idle',
                                                daemon=True))
        for t in self.sentinel_threads:
            t.start()

    def start(self) -> 'BasePod':
        """Start to run all Peas in this BasePod.

        Remember to close the BasePod with :meth:`close`.

        Note that this method has a timeout of ``timeout_ready`` set in CLI,
        which is inherited from :class:`jina.peapods.peas.BasePea`
        """
        # start head and tail
        if self.peas_args['head']:
            p = HeadPea(self.peas_args['head'])
            self.peas.append(p)
            self.enter_context(p)

        if self.peas_args['tail']:
            p = TailPea(self.peas_args['tail'])
            self.peas.append(p)
            self.enter_context(p)

        # start real peas and accumulate the storage id
        if len(self.peas_args['peas']) > 1:
            start_rep_id = 1
            role = PeaRoleType.PARALLEL
        else:
            start_rep_id = 0
            role = PeaRoleType.SINGLETON
        for idx, _args in enumerate(self.peas_args['peas'], start=start_rep_id):
            _args.pea_id = idx
            _args.role = role
            p = Pea(_args, allow_remote=False)
            self.peas.append(p)
            self.enter_context(p)

        self.start_sentinels()
        return self

    @property
    def is_shutdown(self) -> bool:
        return all(not p.is_ready_event.is_set() for p in self.peas)

    def __enter__(self) -> 'BasePod':
        return self.start()

    @property
    def status(self) -> List:
        """The status of a BasePod is the list of status of all its Peas """
        return [p.status for p in self.peas]

    def is_ready(self) -> bool:
        """Wait till the ready signal of this BasePod.

        The pod is ready only when all the contained Peas returns is_ready_event
        """
        for p in self.peas:
            p.is_ready_event.wait()
        return True

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)

    def join(self):
        """Wait until all peas exit"""
        try:
            for s in self.peas:
                s.join()
        except KeyboardInterrupt:
            pass
        finally:
            self.peas.clear()


class MutablePod(BasePod):
    """A :class:`MutablePod` is a pod where all peas and their connections are given"""

    def _parse_args(self, args):
        return args


class FlowPod(BasePod):
    """A :class:`FlowPod` is like a :class:`BasePod`, but it exposes more interfaces for tweaking its connections with
    other Pods, which comes in handy when used in the Flow API.

    .. note::

        Unlike :class:`BasePod`, this class takes a :class:`dict` as the first argument.

    """

    def __init__(self,
                 kwargs: Dict,
                 needs: Set[str] = None,
                 parser: Callable = set_pod_parser,
                 pod_role: 'PodRoleType' = PodRoleType.POD):
        """

        :param kwargs: unparsed argument in dict, if given the
        :param needs: a list of names this BasePod needs to receive message from
        """
        _parser = parser()
        self.cli_args, self._args, self.unk_args = get_parsed_args(kwargs, _parser, 'FlowPod')
        super().__init__(self._args)
        self.needs = needs if needs else set()  #: used in the :class:`jina.flow.Flow` to build the graph
        self._kwargs = get_non_defaults_args(self._args, _parser)
        self.role = pod_role

    def to_cli_command(self):
        if isinstance(self, GatewayPod):
            cmd = 'jina gateway'
        else:
            cmd = 'jina pod'

        return f'{cmd} {" ".join(self.cli_args)}'

    @staticmethod
    def connect(first: 'FlowPod', second: 'FlowPod', first_socket_type: 'SocketType') -> None:
        """Connect two Pods

        :param first: the first BasePod
        :param second: the second BasePod
        :param first_socket_type: socket type of the first BasePod, availables are PUSH_BIND, PUSH_CONNECT, PUB_BIND
        """
        first.tail_args.socket_out = first_socket_type
        second.head_args.socket_in = first.tail_args.socket_out.paired

        if first_socket_type == SocketType.PUSH_BIND:
            first.tail_args.host_out = __default_host__
            second.head_args.host_in = _fill_in_host(bind_args=first.tail_args,
                                                     connect_args=second.head_args)
            second.head_args.port_in = first.tail_args.port_out
        elif first_socket_type == SocketType.PUSH_CONNECT:
            first.tail_args.host_out = _fill_in_host(connect_args=first.tail_args,
                                                     bind_args=second.head_args)
            second.head_args.host_in = __default_host__
            first.tail_args.port_out = second.head_args.port_in
        elif first_socket_type == SocketType.PUB_BIND:
            first.tail_args.host_out = __default_host__  # bind always get default 0.0.0.0
            second.head_args.host_in = _fill_in_host(bind_args=first.tail_args,
                                                     connect_args=second.head_args)  # the hostname of s_pod
            second.head_args.port_in = first.tail_args.port_out
        else:
            raise NotImplementedError(f'{first_socket_type!r} is not supported here')

    def connect_to_tail_of(self, pod: 'BasePod'):
        """Eliminate the head node by connecting prev_args node directly to peas """
        if self._args.parallel > 1 and self.is_head_router:
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
            raise ValueError('the current pod has no head router, deducting the head is confusing')

    def connect_to_head_of(self, pod: 'BasePod'):
        """Eliminate the tail node by connecting next_args node directly to peas """
        if self._args.parallel > 1 and self.is_tail_router:
            # keep the port_out and socket_out of next_arts
            # only reset its input
            pod.head_args = _copy_to_tail_args(pod.head_args,
                                               as_router=False)
            # update peas to receive from it
            self.peas_args['peas'] = _set_peas_args(self._args, self.head_args, pod.head_args)
            # remove the tail node
            self.peas_args['tail'] = None
            # tail is no longer a router anymore
            self.is_tail_router = False
            self.deducted_tail = pod.head_args
        else:
            raise ValueError('the current pod has no tail router, deducting the tail is confusing')

    def start(self) -> 'FlowPod':
        if self._args.host == __default_host__:
            return super().start()
        else:
            if self._args.remote_access == RemoteAccessType.JINAD:
                from .remote import RemoteMutablePod
                _remote_pod = RemoteMutablePod(self.peas_args)
            elif self._args.remote_access == RemoteAccessType.SSH:
                from .ssh import RemoteSSHMutablePod
                _remote_pod = RemoteSSHMutablePod(self.peas_args)
            else:
                raise ValueError(f'{self._args.remote_access} is unsupported')

            self.enter_context(_remote_pod)
            self.start_sentinels()
            return self


def _set_peas_args(args: Namespace, head_args: Namespace = None, tail_args: Namespace = None) -> List[Namespace]:
    result = []
    for _ in range(args.parallel):
        _args = copy.deepcopy(args)
        if head_args:
            _args.port_in = head_args.port_out
        if tail_args:
            _args.port_out = tail_args.port_in
        _args.port_ctrl = random_port()
        _args.identity = get_random_identity()
        _args.log_id = args.log_id
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
        if head_args:
            _args.host_in = _fill_in_host(bind_args=head_args, connect_args=_args)
        if tail_args:
            _args.host_out = _fill_in_host(bind_args=tail_args, connect_args=_args)
        result.append(_args)
    return result


def _set_after_to_pass(args):
    # TODO: I don't remember what is this for? once figure out, this function should be removed
    # remark 1: i think it's related to route driver.
    if hasattr(args, 'polling') and args.polling.is_push:
        # ONLY reset when it is push
        args.uses_after = '_pass'


def _copy_to_head_args(args: Namespace, is_push: bool, as_router: bool = True) -> Namespace:
    """Set the outgoing args of the head router
    """

    _head_args = copy.deepcopy(args)
    _head_args.port_ctrl = random_port()
    _head_args.port_out = random_port()
    _head_args.uses = None
    if is_push:
        if args.scheduling == SchedulerType.ROUND_ROBIN:
            _head_args.socket_out = SocketType.PUSH_BIND
            if as_router:
                _head_args.uses = args.uses_before or '_pass'
        elif args.scheduling == SchedulerType.LOAD_BALANCE:
            _head_args.socket_out = SocketType.ROUTER_BIND
            if as_router:
                _head_args.uses = args.uses_before or '_pass'
    else:
        _head_args.socket_out = SocketType.PUB_BIND
        if as_router:
            _head_args.uses = args.uses_before or '_pass'

    if as_router:
        _head_args.name = args.name or ''
        _head_args.role = PeaRoleType.HEAD

    # in any case, if header is present, it represent this Pod to consume `num_part`
    # the following peas inside the pod will have num_part=1
    args.num_part = 1

    return _head_args


def _copy_to_tail_args(args: Namespace, as_router: bool = True) -> Namespace:
    """Set the incoming args of the tail router
    """
    _tail_args = copy.deepcopy(args)
    _tail_args.port_in = random_port()
    _tail_args.port_ctrl = random_port()
    _tail_args.socket_in = SocketType.PULL_BIND
    _tail_args.uses = None

    if as_router:
        _tail_args.uses = args.uses_after or '_pass'
        _tail_args.name = args.name or ''
        _tail_args.role = PeaRoleType.TAIL
        _tail_args.num_part = 1 if args.polling.is_push else args.parallel

    return _tail_args


def _fill_in_host(bind_args: Namespace, connect_args: Namespace) -> str:
    """Compute the host address for ``connect_args`` """
    from sys import platform

    # by default __default_host__ is 0.0.0.0

    # is BIND at local
    bind_local = (bind_args.host == __default_host__)

    # is CONNECT at local
    conn_local = (connect_args.host == __default_host__)

    # is CONNECT inside docker?
    conn_docker = (getattr(connect_args, 'uses', None) is not None and
                   not is_valid_local_config_source(connect_args.uses))

    # is BIND & CONNECT all on the same remote?
    bind_conn_same_remote = not bind_local and not conn_local and \
                                (bind_args.host == connect_args.host)

    if platform == 'linux' or platform == 'linux2':
        local_host = __default_host__
    else:
        local_host = 'host.docker.internal'

    if bind_local and conn_local and conn_docker:
        return local_host

    if bind_local and conn_local and not conn_docker:
        return __default_host__

    if bind_conn_same_remote:
        if conn_docker:
            return local_host
        else:
            return __default_host__

    if bind_local and not conn_local:
        # in this case we are telling CONN (at remote) our local ip address
        if bind_args.expose_public:
            return get_public_ip()
        else:
            return get_internal_ip()
    else:
        # in this case we (at local) need to know about remote the BIND address
        return bind_args.host


class GatewayPod(BasePod):
    """A :class:`BasePod` that holds a Gateway """

    def start(self) -> 'GatewayPod':
        for s in self.all_args:
            p = RESTGatewayPea(s) if getattr(s, 'rest_api', False) else GatewayPea(s)
            self.peas.append(p)
            self.enter_context(p)

        self.start_sentinels()
        return self


class GatewayFlowPod(GatewayPod, FlowPod):
    """A :class:`FlowPod` that holds a Gateway """

    def __init__(self, kwargs: Dict = None, needs: Set[str] = None):
        FlowPod.__init__(self, kwargs, needs, parser=set_gateway_parser)
        self.role = PodRoleType.GATEWAY
