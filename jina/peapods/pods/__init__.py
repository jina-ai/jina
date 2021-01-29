__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
from argparse import Namespace
from contextlib import ExitStack
from typing import Optional, Dict, List, Union, Set

from .helper import _set_peas_args, _set_after_to_pass, _copy_to_head_args, _copy_to_tail_args, _fill_in_host
from ..peas import BasePea
from ...enums import *


class BasePod(ExitStack):
    """A BasePod is a immutable set of peas, which run in parallel. They share the same input and output socket.
    Internally, the peas can run with the process/thread backend. They can be also run in their own containers
    """

    def __init__(self, args: Union['argparse.Namespace', Dict], needs: Set[str] = None):
        """

        :param args: arguments parsed from the CLI
        """
        super().__init__()
        self.args = args
        BasePod._set_conditional_args(self.args)
        self.needs = needs if needs else set()  #: used in the :class:`jina.flow.Flow` to build the graph

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

        for a in self.all_args:
            BasePod._set_conditional_args(a)

    @property
    def role(self) -> 'PodRoleType':
        return self.args.pod_role

    @property
    def is_singleton(self) -> bool:
        """Return if the Pod contains only a single Pea """
        return not (self.is_head_router or self.is_tail_router)

    @property
    def name(self) -> str:
        """The name of this :class:`BasePod`. """
        return self.args.name

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
        elif (getattr(args, 'uses_before', None) and args.uses_before != '_pass') or (
                getattr(args, 'uses_after', None) and args.uses_after != '_pass'):
            args.scheduling = SchedulerType.ROUND_ROBIN
            if getattr(args, 'uses_before', None):
                self.is_head_router = True
                peas_args['head'] = _copy_to_head_args(args, args.polling.is_push)
            if getattr(args, 'uses_after', None):
                self.is_tail_router = True
                peas_args['tail'] = _copy_to_tail_args(args)
            peas_args['peas'] = _set_peas_args(args, peas_args.get('head', None), peas_args.get('tail', None))
        else:
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
        return ([self.peas_args['head']] if self.peas_args['head'] else []) + \
               ([self.peas_args['tail']] if self.peas_args['tail'] else []) + \
               self.peas_args['peas']

    @property
    def num_peas(self) -> int:
        """Get the number of running :class:`BasePea`"""
        return len(self.peas)

    def __eq__(self, other: 'BasePod'):
        return self.num_peas == other.num_peas and self.name == other.name

    def start(self) -> 'BasePod':
        """Start to run all Peas in this BasePod.

        Remember to close the BasePod with :meth:`close`.

        Note that this method has a timeout of ``timeout_ready`` set in CLI,
        which is inherited from :class:`jina.peapods.peas.BasePea`
        """
        # start head and tail

        for _args in self.all_args:
            self._enter_pea(BasePea(_args))

        return self

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
        if 'pod_role' in args and args.pod_role == PodRoleType.GATEWAY:
            if args.restful:
                args.runtime_cls = 'RESTRuntime'
            else:
                args.runtime_cls = 'GRPCRuntime'

    def connect_to_tail_of(self, pod: 'BasePod'):
        """Eliminate the head node by connecting prev_args node directly to peas """
        if self.args.parallel > 1 and self.is_head_router:
            # keep the port_in and socket_in of prev_args
            # only reset its output
            pod.tail_args = _copy_to_head_args(pod.tail_args, self.args.polling.is_push, as_router=False)
            # update peas to receive from it
            self.peas_args['peas'] = _set_peas_args(self.args, pod.tail_args, self.tail_args)
            # remove the head node
            self.peas_args['head'] = None
            # head is no longer a router anymore
            self.is_head_router = False
            self.deducted_head = pod.tail_args
        else:
            raise ValueError('the current pod has no head router, deducting the head is confusing')

    def connect_to_head_of(self, pod: 'BasePod'):
        """Eliminate the tail node by connecting next_args node directly to peas """
        if self.args.parallel > 1 and self.is_tail_router:
            # keep the port_out and socket_out of next_arts
            # only reset its input
            pod.head_args = _copy_to_tail_args(pod.head_args,
                                               as_router=False)
            # update peas to receive from it
            self.peas_args['peas'] = _set_peas_args(self.args, self.head_args, pod.head_args)
            # remove the tail node
            self.peas_args['tail'] = None
            # tail is no longer a router anymore
            self.is_tail_router = False
            self.deducted_tail = pod.head_args
        else:
            raise ValueError('the current pod has no tail router, deducting the tail is confusing')

    @property
    def is_ready(self) -> bool:
        """A Pod is ready when all the Peas it contains are ready"""
        return all(p.is_ready.is_set() for p in self.peas)
