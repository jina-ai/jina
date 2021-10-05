import copy
import sys
from abc import abstractmethod
from argparse import Namespace
from contextlib import ExitStack
from itertools import cycle
from typing import Dict, Union, Set, List, Optional

from ..networking import get_connect_host
from ..peas import BasePea
from ... import __default_executor__
from ... import helper
from ...enums import (
    SchedulerType,
    PodRoleType,
    SocketType,
    PeaRoleType,
    PollingType,
)
from ...helper import random_identity, CatchAllCleanupContextManager
from ...jaml.helper import complete_path


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


class BasePod:
    """A BasePod is an immutable set of peas. They share the same input and output socket.
    Internally, the peas can run with the process/thread backend.
    They can be also run in their own containers on remote machines.
    """

    def start(self) -> 'BasePod':
        """Start to run all :class:`BasePea` in this BasePod.

        .. note::
            If one of the :class:`BasePea` fails to start, make sure that all of them
            are properly closed.
        """
        raise NotImplementedError

    @staticmethod
    def _set_upload_files(args):
        # sets args.upload_files at the pod level so that peas inherit from it.
        # all peas work under one remote workspace, hence important to have upload_files set for all

        def valid_path(path):
            try:
                complete_path(path)
                return True
            except FileNotFoundError:
                return False

        _upload_files = set()
        for param in ['uses', 'uses_before', 'uses_after']:
            param_value = getattr(args, param, None)
            if param_value and valid_path(param_value):
                _upload_files.add(param_value)

        if getattr(args, 'py_modules', None):
            _upload_files.update(
                {py_module for py_module in args.py_modules if valid_path(py_module)}
            )
        if getattr(args, 'upload_files', None):
            _upload_files.update(
                {
                    upload_file
                    for upload_file in args.upload_files
                    if valid_path(upload_file)
                }
            )
        return list(_upload_files)

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
    def connect_to_predecessor(self) -> str:
        """True, if the Pod should open a connect socket in the HeadPea to the predecessor Pod.
        .. # noqa: DAR201
        """
        return self.args.connect_to_predecessor

    @property
    def head_host(self) -> str:
        """Get the host of the HeadPea of this pod
        .. # noqa: DAR201
        """
        return self.head_args.host

    @property
    def head_port_in(self):
        """Get the port_in of the HeadPea of this pod
        .. # noqa: DAR201
        """
        return self.head_args.port_in

    @property
    def tail_port_out(self):
        """Get the port_out of the TailPea of this pod
        .. # noqa: DAR201
        """
        return self.tail_args.port_out

    @property
    def head_zmq_identity(self):
        """Get the zmq_identity of the HeadPea of this pod
        .. # noqa: DAR201
        """
        return self.head_args.zmq_identity

    def __enter__(self) -> 'BasePod':
        with CatchAllCleanupContextManager(self):
            return self.start()

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

        Pod._set_dynamic_routing_in(_head_args)

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

        Pod._set_dynamic_routing_out(_tail_args)

        return _tail_args

    @property
    @abstractmethod
    def head_args(self) -> Namespace:
        """Get the arguments for the `head` of this BasePod.

        .. # noqa: DAR201
        """
        ...

    @property
    @abstractmethod
    def tail_args(self) -> Namespace:
        """Get the arguments for the `tail` of this BasePod.

        .. # noqa: DAR201
        """
        ...

    @abstractmethod
    def join(self):
        """Wait until all pods and peas exit."""
        ...

    @property
    @abstractmethod
    def _mermaid_str(self) -> List[str]:
        """String that will be used to represent the Pod graphically when `Flow.plot()` is invoked


        .. # noqa: DAR201
        """
        ...

    @property
    def deployments(self) -> List[Dict]:
        """Get deployments of the pod. The BasePod just gives one deployment.

        :return: list of deployments
        """
        return [
            {
                'name': self.name,
                'head_host': self.head_host,
                'head_port_in': self.head_port_in,
                'tail_port_out': self.tail_port_out,
                'head_zmq_identity': self.head_zmq_identity,
            }
        ]


class Pod(BasePod, ExitFIFO):
    """A BasePod is an immutable set of peas, which run in parallel. They share the same input and output socket.
    Internally, the peas can run with the process/thread backend. They can be also run in their own containers
    :param args: arguments parsed from the CLI
    :param needs: pod names of preceding pods, the output of these pods are going into the input of this pod
    """

    def __init__(
        self,
        args: Union['Namespace', Dict],
        needs: Optional[Set[str]] = None,
    ):
        super().__init__()
        args.upload_files = BasePod._set_upload_files(args)
        self.args = args
        self.needs = (
            needs or set()
        )  #: used in the :class:`jina.flow.Flow` to build the graph

        self.is_head_router = False
        self.is_tail_router = False
        self.deducted_head = None
        self.deducted_tail = None
        self.peas = []  # type: List['BasePea']
        self.update_pea_args()
        self._activated = False

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)
        self.join()

    def update_pea_args(self):
        """ Update args of its peas based on Pod args"""
        if isinstance(self.args, Dict):
            # This is used when a Pod is created in a remote context, where peas & their connections are already given.
            self.peas_args = self.args
        else:
            self.peas_args = self._parse_args(self.args)

    @property
    def first_pea_args(self) -> Namespace:
        """Return the first non-head/tail pea's args


        .. # noqa: DAR201
        """
        # note this will be never out of boundary
        return self.peas_args['peas'][0]

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
    def head_args(self) -> Namespace:
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
    def tail_args(self) -> Namespace:
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
            pea.activate_runtime()

        self._activated = True

    def start(self) -> 'BasePod':
        """
        Start to run all :class:`BasePea` in this BasePod.

        :return: started pod

        .. note::
            If one of the :class:`BasePea` fails to start, make sure that all of them
            are properly closed.
        """
        for _args in self._fifo_args:
            if getattr(self.args, 'noblock_on_start', False):
                _args.noblock_on_start = True
            self._enter_pea(BasePea(_args))
        if not getattr(self.args, 'noblock_on_start', False):
            self._activate()
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
                    _args.name += f'/pea-{idx}'
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
                _args.host_in = get_connect_host(
                    bind_host=head_args.host,
                    bind_expose_public=head_args.expose_public,
                    connect_args=_args,
                )
            else:
                Pod._set_dynamic_routing_in(_args)
            if tail_args:
                _args.host_out = get_connect_host(
                    bind_host=tail_args.host,
                    bind_expose_public=tail_args.expose_public,
                    connect_args=_args,
                )
            else:
                Pod._set_dynamic_routing_out(_args)

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
            Pod._set_dynamic_routing_in(args)
            Pod._set_dynamic_routing_out(args)
            parsed_args['peas'] = [args]

        # note that peas_args['peas'][0] exist either way and carries the original property
        return parsed_args

    @staticmethod
    def _set_dynamic_routing_in(args):
        if args.dynamic_routing:
            args.dynamic_routing_in = True
            args.socket_in = SocketType.ROUTER_BIND
            args.zmq_identity = random_identity()

    @staticmethod
    def _set_dynamic_routing_out(args):
        if args.dynamic_routing:
            args.dynamic_routing_out = True
            args.socket_out = SocketType.ROUTER_BIND

    @property
    def _mermaid_str(self) -> List[str]:
        """String that will be used to represent the Pod graphically when `Flow.plot()` is invoked


        .. # noqa: DAR201
        """
        mermaid_graph = []
        if self.role != PodRoleType.GATEWAY and not getattr(
            self.args, 'external', False
        ):
            mermaid_graph = [f'subgraph {self.name};']

            names = [args.name for args in self._fifo_args]
            uses = self.args.uses
            if len(names) == 1:
                mermaid_graph.append(f'{names[0]}/pea-0[{uses}]:::PEA;')
            else:
                mermaid_graph.append(f'\ndirection LR;\n')
                head_name = names[0]
                tail_name = names[-1]
                head_to_show = self.args.uses_before
                if head_to_show is None or head_to_show == __default_executor__:
                    head_to_show = head_name
                tail_to_show = self.args.uses_after
                if tail_to_show is None or tail_to_show == __default_executor__:
                    tail_to_show = tail_name
                for name in names[1:-1]:
                    mermaid_graph.append(
                        f'{head_name}[{head_to_show}]:::HEADTAIL --> {name}[{uses}]:::PEA;'
                    )
                    mermaid_graph.append(
                        f'{name}[{uses}]:::PEA --> {tail_name}[{tail_to_show}]:::HEADTAIL;'
                    )
            mermaid_graph.append('end;')
        return mermaid_graph
