import copy
import sys
from abc import abstractmethod
from argparse import Namespace
from contextlib import ExitStack
from itertools import cycle
from typing import Dict, Union, Set
from typing import List, Optional

from ..peas import BasePea
from ... import __default_host__, __default_executor__
from ... import helper
from ...enums import SchedulerType, PodRoleType, SocketType, PeaRoleType, PollingType
from ...helper import get_public_ip, get_internal_ip, random_identity


class ExitFIFO(ExitStack):
    """
    ExitFIFO changes the exiting order of exitStack to turn it into FIFO.

    .. note::
    The `__exit__` method is copied literally from `ExitStack` and changed the call:
    `is_sync, cb = self._exit_callbacks.pop()` to `is_sync, cb = self._exit_callbacks.popleft()`

    """

    def __exit__(self, *exc_details):
        received_exc = exc_details[0] is not None

        # We manipulate the exception state so it behaves as though
        # we were actually nesting multiple with statements
        frame_exc = sys.exc_info()[1]

        def _fix_exception_context(new_exc, old_exc):
            # Context may not be correct, so find the end of the chain
            while 1:
                exc_context = new_exc.__context__
                if exc_context is old_exc:
                    # Context is already set correctly (see issue 20317)
                    return
                if exc_context is None or exc_context is frame_exc:
                    break
                new_exc = exc_context
            # Change the end of the chain to point to the exception
            # we expect it to reference
            new_exc.__context__ = old_exc

        # Callbacks are invoked in LIFO order to match the behaviour of
        # nested context managers
        suppressed_exc = False
        pending_raise = False
        while self._exit_callbacks:
            is_sync, cb = self._exit_callbacks.popleft()
            assert is_sync
            try:
                if cb(*exc_details):
                    suppressed_exc = True
                    pending_raise = False
                    exc_details = (None, None, None)
            except:
                new_exc_details = sys.exc_info()
                # simulate the stack of exceptions by setting the context
                _fix_exception_context(new_exc_details[1], exc_details[1])
                pending_raise = True
                exc_details = new_exc_details
        if pending_raise:
            try:
                # bare "raise exc_details[1]" replaces our carefully
                # set-up context
                fixed_ctx = exc_details[1].__context__
                raise exc_details[1]
            except BaseException:
                exc_details[1].__context__ = fixed_ctx
                raise
        return received_exc and suppressed_exc


class BasePod(ExitFIFO):
    """A BasePod is an immutable set of peas. They share the same input and output socket.
    Internally, the peas can run with the process/thread backend.
    They can be also run in their own containers on remote machines.
    """

    def __init__(
        self, args: Union['Namespace', Dict], needs: Optional[Set[str]] = None
    ):
        super().__init__()
        self.args = args
        self._set_conditional_args(self.args)
        self.needs = (
            needs if needs else set()
        )  #: used in the :class:`jina.flow.Flow` to build the graph

        self.is_head_router = False
        self.is_tail_router = False
        self.deducted_head = None
        self.deducted_tail = None

    def start(self) -> 'BasePod':
        """Start to run all :class:`BasePea` in this BasePod.

        .. note::
            If one of the :class:`BasePea` fails to start, make sure that all of them
            are properly closed.
        """
        raise NotImplemented()

    def close(self):
        """Stop all :class:`BasePea` in this BasePod.

        .. # noqa: DAR201
        """
        self.__exit__(None, None, None)

    @staticmethod
    def _set_conditional_args(args):
        if args.pod_role == PodRoleType.GATEWAY:
            if args.restful:
                args.runtime_cls = 'RESTRuntime'
            else:
                args.runtime_cls = 'GRPCRuntime'

    @property
    def role(self) -> 'PodRoleType':
        """Return the role of this :class:`BasePod`.

        .. # noqa: DAR201
        """
        return self.args.pod_role

    @property
    def name(self) -> str:
        """The name of this :class:`BasePod`.


        .. # noqa: DAR201
        """
        return self.args.name

    @property
    def host_in(self) -> str:
        """Get the host_in of this pod


        .. # noqa: DAR201
        """
        return self.head_args.host_in

    @property
    def host_out(self) -> str:
        """Get the host_out of this pod


        .. # noqa: DAR201
        """
        return self.tail_args.host_out

    @property
    def address_in(self) -> str:
        """Get the full incoming address of this pod


        .. # noqa: DAR201
        """
        return f'{self.head_args.host_in}:{self.head_args.port_in} ({self.head_args.socket_in!s})'

    @property
    def address_out(self) -> str:
        """Get the full outgoing address of this pod


        .. # noqa: DAR201
        """
        return f'{self.tail_args.host_out}:{self.tail_args.port_out} ({self.tail_args.socket_out!s})'

    def __enter__(self) -> 'BasePod':
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)
        self.join()

    @staticmethod
    def _copy_to_head_args(
        args: Namespace, polling_type: PollingType, as_router: bool = True
    ) -> Namespace:
        """
        Set the outgoing args of the head router

        :param args: basic arguments
        :param polling_type: polling_type can be all or any
        :param as_router: if true, router configuration is applied
        :return: enriched head arguments
        """

        _head_args = copy.deepcopy(args)
        _head_args.polling = polling_type
        _head_args.port_ctrl = helper.random_port()
        _head_args.port_out = helper.random_port()
        _head_args.uses = None
        if polling_type.is_push:
            if args.scheduling == SchedulerType.ROUND_ROBIN:
                _head_args.socket_out = SocketType.PUSH_BIND
            elif args.scheduling == SchedulerType.LOAD_BALANCE:
                _head_args.socket_out = SocketType.ROUTER_BIND
        else:
            _head_args.socket_out = SocketType.PUB_BIND
        if as_router:
            _head_args.uses = args.uses_before or __default_executor__

        if as_router:
            _head_args.pea_role = PeaRoleType.HEAD
            if args.name:
                _head_args.name = f'{args.name}/head'
            else:
                _head_args.name = f'head'

        # in any case, if header is present, it represent this Pod to consume `num_part`
        # the following peas inside the pod will have num_part=1
        args.num_part = 1

        return _head_args

    @staticmethod
    def _copy_to_tail_args(
        args: Namespace, polling_type: PollingType, as_router: bool = True
    ) -> Namespace:
        """
        Set the incoming args of the tail router

        :param args: configuration for the connection
        :param polling_type: polling type can be any or all
        :param as_router: if true, add router configuration
        :return: enriched arguments
        """
        _tail_args = copy.deepcopy(args)
        _tail_args.polling_type = polling_type
        _tail_args.port_in = helper.random_port()
        _tail_args.port_ctrl = helper.random_port()
        _tail_args.socket_in = SocketType.PULL_BIND
        _tail_args.uses = None

        if as_router:
            _tail_args.uses = args.uses_after or __default_executor__
            if args.name:
                _tail_args.name = f'{args.name}/tail'
            else:
                _tail_args.name = f'tail'
            _tail_args.pea_role = PeaRoleType.TAIL
            _tail_args.num_part = 1 if polling_type.is_push else args.parallel

        return _tail_args

    @staticmethod
    def _fill_in_host(bind_args: Namespace, connect_args: Namespace) -> str:
        """
        Compute the host address for ``connect_args``

        :param bind_args: configuration for the host ip binding
        :param connect_args: configuration for the host ip connection
        :return: host ip
        """
        from sys import platform

        # by default __default_host__ is 0.0.0.0

        # is BIND at local
        bind_local = bind_args.host == __default_host__

        # is CONNECT at local
        conn_local = connect_args.host == __default_host__

        # is CONNECT inside docker?
        conn_docker = getattr(
            connect_args, 'uses', None
        ) is not None and connect_args.uses.startswith('docker://')

        # is BIND & CONNECT all on the same remote?
        bind_conn_same_remote = (
            not bind_local and not conn_local and (bind_args.host == connect_args.host)
        )

        if platform in ('linux', 'linux2'):
            local_host = __default_host__
        else:
            local_host = 'host.docker.internal'

        # pod1 in local, pod2 in local (conn_docker if pod2 in docker)
        if bind_local and conn_local:
            return local_host if conn_docker else __default_host__

        # pod1 and pod2 are remote but they are in the same host (pod2 is local w.r.t pod1)
        if bind_conn_same_remote:
            return local_host if conn_docker else __default_host__

        # From here: Missing consideration of docker
        if bind_local and not conn_local:
            # in this case we are telling CONN (at remote) our local ip address
            return get_public_ip() if bind_args.expose_public else get_internal_ip()
        else:
            # in this case we (at local) need to know about remote the BIND address
            return bind_args.host

    @abstractmethod
    def head_args(self):
        """Get the arguments for the `head` of this BasePod.

        .. # noqa: DAR201
        """
        ...

    @abstractmethod
    def tail_args(self):
        """Get the arguments for the `tail` of this BasePod.

        .. # noqa: DAR201
        """
        ...

    @abstractmethod
    def join(self):
        """Wait until all pods and peas exit."""
        ...


class Pod(BasePod):
    """A BasePod is an immutable set of peas, which run in parallel. They share the same input and output socket.
    Internally, the peas can run with the process/thread backend. They can be also run in their own containers
    :param args: arguments parsed from the CLI
    :param needs: pod names of preceding pods, the output of these pods are going into the input of this pod
    """

    def __init__(
        self, args: Union['Namespace', Dict], needs: Optional[Set[str]] = None
    ):
        super().__init__(args, needs)
        self.peas = []  # type: List['BasePea']
        if isinstance(args, Dict):
            # This is used when a Pod is created in a remote context, where peas & their connections are already given.
            self.peas_args = args
        else:
            self.peas_args = self._parse_args(args)
        self._activated = False

    @property
    def is_singleton(self) -> bool:
        """Return if the Pod contains only a single Pea


        .. # noqa: DAR201
        """
        return not (self.is_head_router or self.is_tail_router)

    @property
    def first_pea_args(self) -> Namespace:
        """Return the first non-head/tail pea's args


        .. # noqa: DAR201
        """
        # note this will be never out of boundary
        return self.peas_args['peas'][0]

    @property
    def port_expose(self) -> int:
        """Get the grpc port number


        .. # noqa: DAR201
        """
        return self.first_pea_args.port_expose

    @property
    def host(self) -> str:
        """Get the host name of this Pod


        .. # noqa: DAR201
        """
        return self.first_pea_args.host

    def _parse_args(
        self, args: Namespace
    ) -> Dict[str, Optional[Union[List[Namespace], Namespace]]]:
        return self._parse_base_pod_args(args)

    @property
    def head_args(self):
        """Get the arguments for the `head` of this Pod.


        .. # noqa: DAR201
        """
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
        """Set the arguments for the `head` of this Pod.


        .. # noqa: DAR101
        """
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
        """Get the arguments for the `tail` of this BasePod.

        .. # noqa: DAR201
        """
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
        """Set the arguments for the `tail` of this BasePod.

        .. # noqa: DAR101
        """
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
        """Get all arguments of all Peas in this BasePod.

        .. # noqa: DAR201
        """
        return (
            ([self.peas_args['head']] if self.peas_args['head'] else [])
            + ([self.peas_args['tail']] if self.peas_args['tail'] else [])
            + self.peas_args['peas']
        )

    @property
    def _fifo_args(self) -> List[Namespace]:
        """Get all arguments of all Peas in this BasePod.
        .. # noqa: DAR201
        """
        # For some reason, it seems that using `stack` and having `Head` started after the rest of Peas do not work and
        # some messages are not received by the inner peas. That's why ExitFIFO is needed
        return (
            ([self.peas_args['head']] if self.peas_args['head'] else [])
            + self.peas_args['peas']
            + ([self.peas_args['tail']] if self.peas_args['tail'] else [])
        )

    @property
    def num_peas(self) -> int:
        """Get the number of running :class:`BasePea`

        .. # noqa: DAR201
        """
        return len(self.peas)

    def __eq__(self, other: 'BasePod'):
        return self.num_peas == other.num_peas and self.name == other.name

    def _enter_pea(self, pea: 'BasePea') -> None:
        self.peas.append(pea)
        self.enter_context(pea)

    def _activate(self):
        # order is good. Activate from tail to head
        for pea in reversed(self.peas):
            if pea.args.socket_in == SocketType.DEALER_CONNECT:
                pea.runtime.activate()

        self._activated = True

    def start(self) -> 'BasePod':
        """
        Start to run all :class:`BasePea` in this BasePod.

        :return: started pod

        .. note::
            If one of the :class:`BasePea` fails to start, make sure that all of them
            are properly closed.
        """
        if getattr(self.args, 'noblock_on_start', False):
            for _args in self._fifo_args:
                _args.noblock_on_start = True
                self._enter_pea(BasePea(_args))
            # now rely on higher level to call `wait_start_success`
            return self
        else:
            try:
                for _args in self._fifo_args:
                    self._enter_pea(BasePea(_args))

                self._activate()
            except:
                self.close()
                raise
            return self

    def wait_start_success(self) -> None:
        """Block until all peas starts successfully.

        If not successful, it will raise an error hoping the outer function to catch it
        """

        if not self.args.noblock_on_start:
            raise ValueError(
                f'{self.wait_start_success!r} should only be called when `noblock_on_start` is set to True'
            )

        try:
            for p in self.peas:
                p.wait_start_success()
            self._activate()
        except:
            self.close()
            raise

    def join(self):
        """Wait until all peas exit"""
        try:
            for p in self.peas:
                p.join()
                self._activated = False
        except KeyboardInterrupt:
            pass
        finally:
            self.peas.clear()
            self._activated = False

    @property
    def is_ready(self) -> bool:
        """Checks if Pod is ready

        .. note::
            A Pod is ready when all the Peas it contains are ready


        .. # noqa: DAR201
        """
        return all(p.is_ready.is_set() for p in self.peas) and self._activated

    def _set_after_to_pass(self, args):
        # TODO: check if needed
        # remark 1: i think it's related to route driver.
        if hasattr(args, 'polling') and args.polling.is_push:
            # ONLY reset when it is push
            args.uses_after = __default_executor__

    @staticmethod
    def _set_peas_args(
        args: Namespace,
        head_args: Optional[Namespace] = None,
        tail_args: Namespace = None,
    ) -> List[Namespace]:
        result = []
        _host_list = (
            args.peas_hosts
            if args.peas_hosts
            else [
                args.host,
            ]
        )

        for idx, pea_host in zip(range(args.parallel), cycle(_host_list)):
            _args = copy.deepcopy(args)
            _args.pea_id = idx

            if args.parallel > 1:
                _args.pea_role = PeaRoleType.PARALLEL
                _args.identity = random_identity()
                if _args.peas_hosts:
                    _args.host = pea_host
                if _args.name:
                    _args.name += f'/{idx}'
                else:
                    _args.name = f'{idx}'
            else:
                _args.pea_role = PeaRoleType.SINGLETON

            if head_args:
                _args.port_in = head_args.port_out
            if tail_args:
                _args.port_out = tail_args.port_in
            _args.port_ctrl = helper.random_port()
            _args.socket_out = SocketType.PUSH_CONNECT
            if args.polling.is_push:
                if args.scheduling == SchedulerType.ROUND_ROBIN:
                    _args.socket_in = SocketType.PULL_CONNECT
                elif args.scheduling == SchedulerType.LOAD_BALANCE:
                    _args.socket_in = SocketType.DEALER_CONNECT
                else:
                    raise ValueError(
                        f'{args.scheduling} is not supported as a SchedulerType!'
                    )

            else:
                _args.socket_in = SocketType.SUB_CONNECT
            if head_args:
                _args.host_in = BasePod._fill_in_host(
                    bind_args=head_args, connect_args=_args
                )
            if tail_args:
                _args.host_out = BasePod._fill_in_host(
                    bind_args=tail_args, connect_args=_args
                )

            # pea workspace if not set then derive from workspace
            if not _args.workspace:
                _args.workspace = args.workspace
            result.append(_args)
        return result

    def _parse_base_pod_args(self, args):
        parsed_args = {'head': None, 'tail': None, 'peas': []}
        if getattr(args, 'parallel', 1) > 1:
            # reasons to separate head and tail from peas is that they
            # can be deducted based on the previous and next pods
            self.is_head_router = True
            self.is_tail_router = True
            parsed_args['head'] = BasePod._copy_to_head_args(args, args.polling)
            parsed_args['tail'] = BasePod._copy_to_tail_args(args, args.polling)
            parsed_args['peas'] = self._set_peas_args(
                args,
                head_args=parsed_args['head'],
                tail_args=parsed_args['tail'],
            )
        elif (
            getattr(args, 'uses_before', None)
            and args.uses_before != __default_executor__
        ) or (
            getattr(args, 'uses_after', None)
            and args.uses_after != __default_executor__
        ):
            args.scheduling = SchedulerType.ROUND_ROBIN
            if getattr(args, 'uses_before', None):
                self.is_head_router = True
                parsed_args['head'] = self._copy_to_head_args(args, args.polling)
            if getattr(args, 'uses_after', None):
                self.is_tail_router = True
                parsed_args['tail'] = self._copy_to_tail_args(args, args.polling)
            parsed_args['peas'] = self._set_peas_args(
                args,
                head_args=parsed_args.get('head', None),
                tail_args=parsed_args.get('tail', None),
            )
        else:
            self.is_head_router = False
            self.is_tail_router = False
            parsed_args['peas'] = [args]

        # note that peas_args['peas'][0] exist either way and carries the original property
        return parsed_args
