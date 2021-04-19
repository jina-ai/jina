__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
from argparse import Namespace
from typing import Optional, Dict, List, Union, Set

from .. import Pea
from .. import Pod
from .. import BasePod
from ...enums import PollingType, SchedulerType, PodRoleType, PeaRoleType


class CompoundPod(BasePod):
    """A CompoundPod is a immutable set of pods, which run in parallel. They share the same input and output socket.
    Internally, the peas of the pods can run with the process/thread backend. They can be also run in their own containers.
    :param args: arguments parsed from the CLI
    :param needs: pod names of preceding pods, the output of these pods are going into the input of this pod
    """

    def __init__(self, args: Union['argparse.Namespace', Dict], needs: Set[str] = None):
        super().__init__(args, needs)
        self.replica_list = []  # type: List['Pod']
        if isinstance(args, Dict):
            # This is used when a Pod is created in a remote context, where peas & their connections are already given.
            self.replicas_args = args
        else:
            self.replicas_args = self._parse_args(args)

    @property
    def first_pod_args(self) -> Namespace:
        """
        Return the first non-head/tail pod args

        :return: arguments of the first pod
        """
        # note this will be never out of boundary
        return self.replicas_args['replicas'][0]

    def _parse_args(
        self, args: Namespace
    ) -> Dict[str, Optional[Union[List[Namespace], Namespace]]]:
        return self._parse_base_pod_args(
            args,
            attribute='replicas',
            id_attribute_name='replica_id',
            role_type=PeaRoleType.REPLICA,
            repetition_attribute='replicas',
            polling_type=PollingType.ANY,
        )

    @property
    def head_args(self):
        """
        Get the arguments for the `head` of this BasePod.

        :return: arguments of the head pea
        """
        if self.is_head_router and self.replicas_args['head']:
            return self.replicas_args['head']
        elif not self.is_head_router and len(self.replicas_args['replicas']) == 1:
            return self.first_pod_args
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
            return self.first_pod_args
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
        return sum([replica.num_peas for replica in self.replica_list]) + len(self.peas)

    def __eq__(self, other: 'CompoundPod'):
        return self.num_peas == other.num_peas and self.name == other.name

    def start(self) -> 'CompoundPod':
        """
        Start to run all :class:`Pod` and :class:`Pea` in this CompoundPod.

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
        Block until all pods and peas start successfully.
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

    def join(self):
        """Wait until all pods and peas exit."""
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

    def _set_after_to_pass(self, args):
        if PollingType.ANY.is_push:
            # ONLY reset when it is push
            args.uses_after = '_pass'

    def rolling_update(self):
        """
        Update all pods of this compound pod.
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
