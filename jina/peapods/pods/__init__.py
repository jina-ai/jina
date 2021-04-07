__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
from argparse import Namespace
from contextlib import ExitStack
from typing import Optional, Dict, List, Union, Set

from jina.peapods.zmq import send_ctrl_message
from jina.types.message.dump import DumpMessage

from .helper import (
    _set_peas_args,
    _set_after_to_pass,
    _copy_to_head_args,
    _copy_to_tail_args,
    _fill_in_host,
)
from ..peas import BasePea
from ...enums import *


class BasePod(ExitStack):
    """A BasePod is a immutable set of peas, which run in parallel. They share the same input and output socket.
    Internally, the peas can run with the process/thread backend. They can be also run in their own containers
    :param args: arguments parsed from the CLI
    :param needs: pod names of preceding pods, the output of these pods are going into the input of this pod
    """

    def __init__(self, args: Union['argparse.Namespace', Dict], needs: Set[str] = None):
        super().__init__()
        self.args = args
        self._set_conditional_args(self.args)
        self.needs = (
            needs if needs else set()
        )  #: used in the :class:`jina.flow.Flow` to build the graph

        self.peas = []  # type: List['BasePea']
        self.is_head_router = False
        self.is_tail_router = False
        self.deducted_head = None
        self.deducted_tail = None

        if isinstance(args, Dict):
            # This is used when a Pod is created in a remote context, where peas & their connections are already given.
            self.peas_args = args
        else:
            self.peas_args = self._parse_args(args)

    @property
    def role(self) -> 'PodRoleType':
        """Return the role of this :class:`BasePod`.


        .. # noqa: DAR201
        """
        return self.args.pod_role

    @property
    def is_singleton(self) -> bool:
        """Return if the Pod contains only a single Pea


        .. # noqa: DAR201
        """
        return not (self.is_head_router or self.is_tail_router)

    @property
    def name(self) -> str:
        """The name of this :class:`BasePod`.


        .. # noqa: DAR201
        """
        return self.args.name

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

    @property
    def first_pea_args(self) -> Namespace:
        """Return the first non-head/tail pea's args


        .. # noqa: DAR201
        """
        # note this will be never out of boundary
        return self.peas_args['peas'][0]

    def _parse_args(
        self, args: Namespace
    ) -> Dict[str, Optional[Union[List[Namespace], Namespace]]]:
        peas_args = {'head': None, 'tail': None, 'peas': []}
        if getattr(args, 'parallel', 1) > 1:
            # reasons to separate head and tail from peas is that they
            # can be deducted based on the previous and next pods
            _set_after_to_pass(args)
            self.is_head_router = True
            self.is_tail_router = True
            peas_args['head'] = _copy_to_head_args(args, args.polling.is_push)
            peas_args['tail'] = _copy_to_tail_args(args)
            peas_args['peas'] = _set_peas_args(
                args, peas_args['head'], peas_args['tail']
            )
        elif (getattr(args, 'uses_before', None) and args.uses_before != '_pass') or (
            getattr(args, 'uses_after', None) and args.uses_after != '_pass'
        ):
            args.scheduling = SchedulerType.ROUND_ROBIN
            if getattr(args, 'uses_before', None):
                self.is_head_router = True
                peas_args['head'] = _copy_to_head_args(args, args.polling.is_push)
            if getattr(args, 'uses_after', None):
                self.is_tail_router = True
                peas_args['tail'] = _copy_to_tail_args(args)
            peas_args['peas'] = _set_peas_args(
                args, peas_args.get('head', None), peas_args.get('tail', None)
            )
        else:
            self.is_head_router = False
            self.is_tail_router = False
            peas_args['peas'] = [args]

        # note that peas_args['peas'][0] exist either way and carries the original property
        return peas_args

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

    def _enter_pea(self, pea: 'BasePea') -> None:
        self.peas.append(pea)
        self.enter_context(pea)

    def __enter__(self) -> 'BasePod':
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)
        self.join()

    def join(self):
        """Wait until all peas exit"""
        try:
            for p in self.peas:
                p.join()
        except KeyboardInterrupt:
            pass
        finally:
            self.peas.clear()

    @staticmethod
    def _set_conditional_args(args):
        if args.pod_role == PodRoleType.GATEWAY:
            if args.restful:
                args.runtime_cls = 'RESTRuntime'
            else:
                args.runtime_cls = 'GRPCRuntime'

    @property
    def is_ready(self) -> bool:
        """Checks if Pod is ready

        .. note::
            A Pod is ready when all the Peas it contains are ready


        .. # noqa: DAR201
        """
        return all(p.is_ready.is_set() for p in self.peas)

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
