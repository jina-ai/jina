__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
from argparse import Namespace
from typing import Optional, Dict, List, Union, Set

from .helper import (
    _set_pod_args,
    _set_after_to_pass,
    _copy_to_head_args,
    _copy_to_tail_args,
    _fill_in_host,
)
from .. import Pea
from .. import Pod
from .. import BasePod
from ...enums import *


class CompoundPod(BasePod):
    """A BasePod is a immutable set of peas, which run in parallel. They share the same input and output socket.
    Internally, the peas can run with the process/thread backend. They can be also run in their own containers
    """

    def __init__(self, args: Union['argparse.Namespace', Dict], needs: Set[str] = None):
        """
        :param args: arguments parsed from the CLI
        :param needs: pod names of preceding pods, the output of these pods are going into the input of this pod
        """
        super().__init__()

        self.args = args
        self._set_conditional_args(self.args)
        self.needs = (
            needs if needs else set()
        )  #: used in the :class:`jina.flow.Flow` to build the graph

        self.replica_list = []  # type: List['Pod']
        self.peas = []  # type: List['Pea']
        self.is_head_router = False
        self.is_tail_router = False
        self.deducted_head = None
        self.deducted_tail = None

        if isinstance(args, Dict):
            # This is used when a Pod is created in a remote context, where peas & their connections are already given.
            self.replicas_args = args
        else:
            self.replicas_args = self._parse_args(args)

    @property
    def role(self) -> 'PodRoleType':
        """
        Return the role of this :class:`CompoundPod`.

        :return: role type
        """
        return self.args.pod_role

    @property
    def is_singleton(self) -> bool:
        """
        Return if the Pod contains only a single Pea

        :return: true if there is only one replica, else false
        """
        return not (self.is_head_router or self.is_tail_router)

    @property
    def name(self) -> str:
        """
        The name of this :class:`CompoundPod`.

        :return: name of the pod
        """
        return self.args.name

    @property
    def port_expose(self) -> int:
        """
        Get the grpc port number.

        :return: exposed port
        """
        return self.first_pea_args.port_expose

    @property
    def host(self) -> str:
        """
        Get the host name of this Pod.

        :return: host name
        """
        return self.first_pea_args.host

    @property
    def host_in(self) -> str:
        """
        Get the host_in of this pod.

        :return: host name of incoming requests
        """
        return self.head_args.host_in

    @property
    def host_out(self) -> str:
        """
        Get the host_out of this pod.

        :return: host name of outgoing requests
        """
        return self.tail_args.host_out

    @property
    def address_in(self) -> str:
        """
        Get the full incoming address of this pod.

        :return: address for incoming requests
        """
        return f'{self.head_args.host_in}:{self.head_args.port_in} ({self.head_args.socket_in!s})'

    @property
    def address_out(self) -> str:
        """
        Get the full outgoing address of this pod.

        :return: address for outgoing requests.
        """
        return f'{self.tail_args.host_out}:{self.tail_args.port_out} ({self.tail_args.socket_out!s})'

    @property
    def first_pea_args(self) -> Namespace:
        """
        Return the first non-head/tail pea's args

        :return: arguments of the first pea which is not a head pea or tail pea
        """
        # note this will be never out of boundary
        return self.replicas_args['replicas'][0]

    def _parse_args(
        self, args: Namespace
    ) -> Dict[str, Optional[Union[List[Namespace], Namespace]]]:
        replicas_args = {'head': None, 'tail': None, 'replicas': []}
        if getattr(args, 'replicas', 1) > 1:
            # reasons to separate head and tail from peas is that they
            # can be deducted based on the previous and next pods
            _set_after_to_pass(args)
            self.is_head_router = True
            self.is_tail_router = True
            replicas_args['head'] = _copy_to_head_args(args, PollingType.ANY.is_push)
            replicas_args['tail'] = _copy_to_tail_args(args)
            replicas_args['replicas'] = _set_pod_args(
                args, replicas_args['head'], replicas_args['tail']
            )

        elif (getattr(args, 'uses_before', None) and args.uses_before != '_pass') or (
            getattr(args, 'uses_after', None) and args.uses_after != '_pass'
        ):
            args.scheduling = SchedulerType.ROUND_ROBIN
            if getattr(args, 'uses_before', None):
                self.is_head_router = True
                replicas_args['head'] = _copy_to_head_args(
                    args, PollingType.ANY.is_push
                )
            if getattr(args, 'uses_after', None):
                self.is_tail_router = True
                replicas_args['tail'] = _copy_to_tail_args(args)
            replicas_args['replicas'] = _set_pod_args(
                args, replicas_args.get('head', None), replicas_args.get('tail', None)
            )
        else:
            self.is_head_router = False
            self.is_tail_router = False
            replicas_args['replicas'] = [args]

        # note that replicas_args['replicas'][0] exist either way and carries the original property
        return replicas_args

    @property
    def head_args(self):
        """
        Get the arguments for the `head` of this BasePod.

        :return: arguments of the head pea
        """
        if self.is_head_router and self.replicas_args['head']:
            return self.replicas_args['head']
        elif not self.is_head_router and len(self.replicas_args['replicas']) == 1:
            return self.first_pea_args
        elif self.deducted_head:
            return self.deducted_head
        else:
            raise ValueError('ambiguous head node, maybe it is deducted already?')

    @head_args.setter
    def head_args(self, args):
        """
        Set the arguments for the `head` of this BasePod.

        :param args: arguments of the head pea
        """
        if self.is_head_router and self.replicas_args['head']:
            self.replicas_args['head'] = args
        elif not self.is_head_router and len(self.replicas_args['replicas']) == 1:
            self.replicas_args['replicas'][0] = args  # weak reference
        elif self.deducted_head:
            self.deducted_head = args
        else:
            raise ValueError('ambiguous head node, maybe it is deducted already?')

    @property
    def tail_args(self):
        """
        Get the arguments for the `tail` of this BasePod.

        :return: arguments of the tail pea
        """
        if self.is_tail_router and self.replicas_args['tail']:
            return self.replicas_args['tail']
        elif not self.is_tail_router and len(self.replicas_args['replicas']) == 1:
            return self.first_pea_args
        elif self.deducted_tail:
            return self.deducted_tail
        else:
            raise ValueError('ambiguous tail node, maybe it is deducted already?')

    @tail_args.setter
    def tail_args(self, args):
        """
        Set the arguments for the `tail` of this BasePod.

        :param args: arguments of the tail pea
        """
        if self.is_tail_router and self.replicas_args['tail']:
            self.replicas_args['tail'] = args
        elif not self.is_tail_router and len(self.replicas_args['replicas']) == 1:
            self.replicas_args['replicas'][0] = args  # weak reference
        elif self.deducted_tail:
            self.deducted_tail = args
        else:
            raise ValueError('ambiguous tail node, maybe it is deducted already?')

    @property
    def all_args(
        self,
    ) -> Dict[
        str,
        Union[
            List[Union[List[Namespace], Namespace, None]],
            list,
            List[Namespace],
            Namespace,
            None,
        ],
    ]:
        """
        Get all arguments of all Peas and Pods (replicas) in this CompoundPod.

        :return: arguments for all Peas and pods
        """
        args = {
            'peas': ([self.replicas_args['head']] if self.replicas_args['head'] else [])
            + ([self.replicas_args['tail']] if self.replicas_args['tail'] else []),
            'replicas': self.replicas_args['replicas'],
        }
        return args

    @property
    def num_peas(self) -> int:
        """
        Get the number of running :class:`Pod`

        :return: total number of peas including head and tail
        """
        return len(self.replica_list)

    def __eq__(self, other: 'CompoundPod'):
        return self.num_peas == other.num_peas and self.name == other.name

    def start(self) -> 'CompoundPod':
        """
        Start to run all :class:`Pod` in this CompoundPod.

        :return: started CompoundPod

        .. note::
            If one of the :class:`Pod` fails to start, make sure that all of them
            are properly closed.
        """
        if getattr(self.args, 'noblock_on_start', False):
            for _args in self.all_args['peas']:
                _args.noblock_on_start = True
                self._enter_pea(Pea(_args))
            for _args in self.all_args['replicas']:
                _args.noblock_on_start = True
                _args.polling = PollingType.ALL
                self._enter_replica(Pod(_args))

            # now rely on higher level to call `wait_start_success`
            return self
        else:
            try:
                for _args in self.all_args['peas']:
                    self._enter_pea(Pea(_args))
                for _args in self.all_args['replicas']:
                    self._enter_replica(Pod(_args))
            except:
                self.close()
                raise
            return self

    def wait_start_success(self) -> None:
        """
        Block until all peas starts successfully.
        If not successful, it will raise an error hoping the outer function to catch it
        """

        if not self.args.noblock_on_start:
            raise ValueError(
                f'{self.wait_start_success!r} should only be called when `noblock_on_start` is set to True'
            )

        try:
            for p in self.peas:
                p.wait_start_success()
            for p in self.replica_list:
                p.wait_start_success()
        except:
            self.close()
            raise

    def _enter_replica(self, replica: 'Pod') -> None:
        self.replica_list.append(replica)
        self.enter_context(replica)

    def _enter_pea(self, pea: 'Pea') -> None:
        self.peas.append(pea)
        self.enter_context(pea)

    def __enter__(self) -> 'CompoundPod':
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)
        self.join()

    def join(self):
        """Wait until all peas exit."""
        try:
            for p in self.peas:
                p.join()
            for p in self.replica_list:
                p.join()
        except KeyboardInterrupt:
            pass
        finally:
            self.peas.clear()
            self.replica_list.clear()

    @staticmethod
    def _set_conditional_args(args):
        if args.pod_role == PodRoleType.GATEWAY:
            if args.restful:
                args.runtime_cls = 'RESTRuntime'
            else:
                args.runtime_cls = 'GRPCRuntime'

    @property
    def is_ready(self) -> bool:
        """
        Checks if Pod is read.
        :return: true if the peas and pods are ready to serve requests

        .. note::
            A Pod is ready when all the Peas it contains are ready
        """
        return all(
            [p.is_ready.is_set() for p in self.peas]
            + [p.is_ready.is_set() for p in self.replica_list]
        )

    def rolling_update(self):
        """
        Update all replicas of this compound pod.
        """
        for i in range(len(self.replica_list)):
            replica = self.replica_list[i]
            replica.close()
            del replica
            _args = self.all_args['replicas'][i]
            _args.noblock_on_start = False
            new_replica = Pod(_args)
            self.enter_context(new_replica)
            self.replica_list[i] = new_replica
