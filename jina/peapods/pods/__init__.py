__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
from argparse import Namespace
from contextlib import ExitStack
from typing import Optional, Dict, List, Union, Set

from jina.peapods.zmq import send_ctrl_message
from jina.types.message.dump import DumpMessage

import copy
from argparse import Namespace
from typing import List, Optional
from itertools import cycle

from ... import __default_host__
from ...enums import SchedulerType, SocketType, PeaRoleType, PollingType
from ...helper import get_public_ip, get_internal_ip, random_identity
from ... import helper

from ..peas import BasePea
from ...enums import SchedulerType, PodRoleType


class BasePod(ExitStack):
    """A BasePod is an immutable set of peas. They share the same input and output socket.
    Internally, the peas can run with the process/thread backend.
    They can be also run in their own containers on remote machines.
    """

    def __init__(self, args: Union['argparse.Namespace', Dict], needs: Set[str] = None):
        super().__init__()
        self.peas = []  # type: List['BasePea']
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
        """Stop all :class:`BasePea` in this BasePod."""
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

    def _parse_base_pod_args(
        self,
        args,
        attribute,
        id_attribute_name,
        role_type,
        repetition_attribute,
        polling_type,
    ):
        parsed_args = {'head': None, 'tail': None, attribute: []}
        if getattr(args, repetition_attribute, 1) > 1:
            # reasons to separate head and tail from peas is that they
            # can be deducted based on the previous and next pods
            self._set_after_to_pass(args)
            self.is_head_router = True
            self.is_tail_router = True
            parsed_args['head'] = BasePod._copy_to_head_args(args, polling_type.is_push)
            parsed_args['tail'] = BasePod._copy_to_tail_args(args, polling_type.is_push)
            parsed_args[attribute] = BasePod._set_peas_args(
                args,
                role_type=role_type,
                repetition_attribute=repetition_attribute,
                id_attribute_name=id_attribute_name,
                polling_type=polling_type,
                head_args=parsed_args['head'],
                tail_args=parsed_args['tail'],
            )
        elif (getattr(args, 'uses_before', None) and args.uses_before != '_pass') or (
            getattr(args, 'uses_after', None) and args.uses_after != '_pass'
        ):
            args.scheduling = SchedulerType.ROUND_ROBIN
            if getattr(args, 'uses_before', None):
                self.is_head_router = True
                parsed_args['head'] = self._copy_to_head_args(
                    args, polling_type.is_push
                )
            if getattr(args, 'uses_after', None):
                self.is_tail_router = True
                parsed_args['tail'] = self._copy_to_tail_args(
                    args, polling_type.is_push
                )
            parsed_args[attribute] = self._set_peas_args(
                args,
                role_type=role_type,
                repetition_attribute=repetition_attribute,
                id_attribute_name=id_attribute_name,
                polling_type=polling_type,
                head_args=parsed_args.get('head', None),
                tail_args=parsed_args.get('tail', None),
            )
        else:
            self.is_head_router = False
            self.is_tail_router = False
            parsed_args[attribute] = [args]

        # note that peas_args['peas'][0] exist either way and carries the original property
        return parsed_args

    def _enter_pea(self, pea: 'BasePea') -> None:
        self.peas.append(pea)
        self.enter_context(pea)

    def __enter__(self) -> 'BasePod':
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)
        self.join()

    @staticmethod
    def _set_peas_args(
        args: Namespace,
        role_type: PeaRoleType,
        repetition_attribute: str,
        id_attribute_name: str,
        polling_type: PollingType,
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

        for idx, pea_host in zip(
            range(getattr(args, repetition_attribute)), cycle(_host_list)
        ):
            _args = copy.deepcopy(args)

            setattr(_args, id_attribute_name, idx)

            if getattr(args, repetition_attribute) > 1:
                _args.pea_role = role_type
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
            if polling_type.is_push:
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

            result.append(_args)
        return result

    @staticmethod
    def _set_after_to_pass(args):
        raise NotImplemented

    @staticmethod
    def _copy_to_head_args(
        args: Namespace, is_push: bool, as_router: bool = True
    ) -> Namespace:
        """
        Set the outgoing args of the head router

        :param args: basic arguments
        :param is_push: if true, set socket_out based on the SchedulerType
        :param as_router: if true, router configuration is applied
        :return: enriched head arguments
        """

        _head_args = copy.deepcopy(args)
        _head_args.port_ctrl = helper.random_port()
        _head_args.port_out = helper.random_port()
        _head_args.uses = None
        if is_push:
            if args.scheduling == SchedulerType.ROUND_ROBIN:
                _head_args.socket_out = SocketType.PUSH_BIND
            elif args.scheduling == SchedulerType.LOAD_BALANCE:
                _head_args.socket_out = SocketType.ROUTER_BIND
        else:
            _head_args.socket_out = SocketType.PUB_BIND
        if as_router:
            _head_args.uses = args.uses_before or '_pass'

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
        args: Namespace, is_push: bool, as_router: bool = True
    ) -> Namespace:
        """
        Set the incoming args of the tail router

        :param args: configuration for the connection
        :param is_push: if true, set socket_out based on the SchedulerType
        :param as_router: if true, add router configuration
        :return: enriched arguments
        """
        _tail_args = copy.deepcopy(args)
        _tail_args.port_in = helper.random_port()
        _tail_args.port_ctrl = helper.random_port()
        _tail_args.socket_in = SocketType.PULL_BIND
        _tail_args.uses = None

        if as_router:
            _tail_args.uses = args.uses_after or '_pass'
            if args.name:
                _tail_args.name = f'{args.name}/tail'
            else:
                _tail_args.name = f'tail'
            _tail_args.pea_role = PeaRoleType.TAIL
            _tail_args.num_part = 1 if is_push else args.parallel

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


class Pod(BasePod):
    """A BasePod is an immutable set of peas, which run in parallel. They share the same input and output socket.
    Internally, the peas can run with the process/thread backend. They can be also run in their own containers
    :param args: arguments parsed from the CLI
    :param needs: pod names of preceding pods, the output of these pods are going into the input of this pod
    """

    def __init__(self, args: Union['argparse.Namespace', Dict], needs: Set[str] = None):
        super().__init__(args, needs)
        if isinstance(args, Dict):
            # This is used when a Pod is created in a remote context, where peas & their connections are already given.
            self.peas_args = args
        else:
            self.peas_args = self._parse_args(args)

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
        return self._parse_base_pod_args(
            args,
            attribute='peas',
            id_attribute_name='pea_id',
            role_type=PeaRoleType.PARALLEL,
            repetition_attribute='parallel',
            polling_type=getattr(args, 'polling', None),
        )

    @property
    def head_args(self):
        """Get the arguments for the `head` of this BasePod.


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
        """Set the arguments for the `head` of this BasePod.


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
    def num_peas(self) -> int:
        """Get the number of running :class:`BasePea`

        .. # noqa: DAR201
        """
        return len(self.peas)

    def __eq__(self, other: 'BasePod'):
        return self.num_peas == other.num_peas and self.name == other.name

    def start(self) -> 'BasePod':
        """
        Start to run all :class:`BasePea` in this BasePod.

        :return: started pod

        .. note::
            If one of the :class:`BasePea` fails to start, make sure that all of them
            are properly closed.
        """
        if getattr(self.args, 'noblock_on_start', False):
            for _args in self.all_args:
                _args.noblock_on_start = True
                self._enter_pea(BasePea(_args))
            # now rely on higher level to call `wait_start_success`
            return self
        else:
            try:
                for _args in self.all_args:
                    self._enter_pea(BasePea(_args))
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
        except:
            self.close()
            raise

    def join(self):
        """Wait until all peas exit"""
        try:
            for p in self.peas:
                p.join()
        except KeyboardInterrupt:
            pass
        finally:
            self.peas.clear()

    @property
    def is_ready(self) -> bool:
        """Checks if Pod is ready

        .. note::
            A Pod is ready when all the Peas it contains are ready


        .. # noqa: DAR201
        """
        return all(p.is_ready.is_set() for p in self.peas)

    def _set_after_to_pass(self, args):
        # TODO: check if needed
        # remark 1: i think it's related to route driver.
        if hasattr(args, 'polling') and args.polling.is_push:
            # ONLY reset when it is push
            args.uses_after = '_pass'

    def dump(self, path, shards, timeout):
        """Emit a Dump request to its Peas

        :param shards: the nr of shards in the dump
        :param path: the path to which to dump
        :param timeout: time to wait (seconds)
        """
        for pea in self.peas:
            if 'head' not in pea.name and 'tail' not in pea.name:
                send_ctrl_message(
                    pea.runtime.ctrl_addr,
                    DumpMessage(path=path, shards=shards),
                    timeout=timeout,
                )
