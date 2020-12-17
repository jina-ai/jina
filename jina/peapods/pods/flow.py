from typing import Dict, Set, Callable

from . import BasePod
from .helper import _fill_in_host, _copy_to_head_args, _set_peas_args, _copy_to_tail_args
from ... import __default_host__
from ...enums import PodRoleType, SocketType, RemoteAccessType
from ...helper import get_parsed_args, get_non_defaults_args
from ...parser import set_pod_parser


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
        self.cli_args, self._args, self.unk_args = get_parsed_args(kwargs, _parser)
        super().__init__(self._args)
        self.needs = needs if needs else set()  #: used in the :class:`jina.flow.Flow` to build the graph
        self._kwargs = get_non_defaults_args(self._args, _parser)
        self.role = pod_role

    def to_cli_command(self):
        from .gateway import GatewayPod
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
                from jina.peapods.runtimes.remote.jinad import JinadRemoteRuntime
                _remote_runtime = JinadRemoteRuntime(self.peas_args, kind='pod')
            elif self._args.remote_access == RemoteAccessType.SSH:
                from jina.peapods.runtimes.remote.ssh import SSHRuntime
                _remote_runtime = SSHRuntime(self.peas_args, kind='pod')
            else:
                raise ValueError(f'{self._args.remote_access} is unsupported')

            self.enter_context(_remote_runtime)
            self.start_sentinels()
            return self
