__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import copy
from argparse import Namespace
from itertools import cycle
from typing import Optional, Dict, List, Union, Set

from .. import BasePod
from .. import Pea
from .. import Pod
from ... import helper
from ...enums import PollingType, SocketType, SchedulerType
from ...helper import random_identity


class CompoundPod(BasePod):
    """A CompoundPod is a immutable set of pods, which run in parallel.
    A CompoundPod is an abstraction using a composable pattern to abstract the usage of parallel Pods that act as replicas.

    CompoundPod will make sure to add a `HeadPea` and a `TailPea` to serve as routing/merging pattern for the different Pod replicas

    :param args: pod arguments parsed from the CLI. These arguments will be used for each of the replicas
    :param needs: pod names of preceding pods, the output of these pods are going into the input of this pod
    """

    def __init__(
        self, args: Union['Namespace', Dict], needs: Optional[Set[str]] = None
    ):
        super().__init__(args, needs)
        self.replica_list = []  # type: List['Pod']
        if isinstance(args, Dict):
            # This is used when a Pod is created in a remote context, where peas & their connections are already given.
            self.replicas_args = args
        else:
            self.replicas_args = self._parse_args(args)

    @property
    def port_expose(self) -> int:
        """Get the grpc port number

        .. # noqa: DAR201
        """
        return self.head_args.port_expose

    @property
    def host(self) -> str:
        """Get the host name of this Pod

        .. # noqa: DAR201
        """
        return self.head_args.host

    def _parse_args(
        self, args: Namespace
    ) -> Dict[str, Optional[Union[List[Namespace], Namespace]]]:
        parsed_args = {'head': None, 'tail': None, 'replicas': []}
        # reasons to separate head and tail from peas is that they
        # can be deducted based on the previous and next pods
        self._set_after_to_pass(args)
        self.is_head_router = True
        self.is_tail_router = True
        parsed_args['head'] = BasePod._copy_to_head_args(args, PollingType.ANY)
        parsed_args['tail'] = BasePod._copy_to_tail_args(args, PollingType.ANY)
        parsed_args['replicas'] = self._set_replica_args(
            args,
            head_args=parsed_args['head'],
            tail_args=parsed_args['tail'],
        )
        return parsed_args

    @property
    def head_args(self):
        """
        Get the arguments for the `head` of this BasePod.

        :return: arguments of the head pea
        """
        return self.replicas_args['head']

    @head_args.setter
    def head_args(self, args):
        """
        Set the arguments for the `head` of this BasePod.

        :param args: arguments of the head pea
        """
        self.replicas_args['head'] = args

    @property
    def tail_args(self):
        """
        Get the arguments for the `tail` of this BasePod.

        :return: arguments of the tail pea
        """
        return self.replicas_args['tail']

    @tail_args.setter
    def tail_args(self, args):
        """
        Set the arguments for the `tail` of this BasePod.

        :param args: arguments of the tail pea
        """
        self.replicas_args['tail'] = args

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
            + [p.is_ready for p in self.replica_list]
        )

    def _set_after_to_pass(self, args):
        if PollingType.ANY.is_push:
            # ONLY reset when it is push
            args.uses_after = '_pass'

    @staticmethod
    def _set_replica_args(
        args: Namespace,
        head_args: Namespace,
        tail_args: Namespace,
    ) -> List[Namespace]:
        """
        Sets the arguments of the replicas in the compound pod.

        :param args: arguments configured by the user for the replicas
        :param head_args: head args from the compound pod
        :param tail_args: tail args from the compound pod

        :return: list of arguments for the replicas
        """
        result = []
        _host_list = (
            args.peas_hosts
            if args.peas_hosts
            else [
                args.host,
            ]
        )
        host_generator = cycle(_host_list)
        for idx in range(args.replicas):
            _args = copy.deepcopy(args)
            pod_host_list = [
                host for _, host in zip(range(args.parallel), host_generator)
            ]
            _args.peas_hosts = pod_host_list
            _args.replica_id = idx
            _args.identity = random_identity()
            if _args.name:
                _args.name += f'/{idx}'
            else:
                _args.name = f'{idx}'

            _args.port_in = head_args.port_out
            _args.port_out = tail_args.port_in
            _args.port_ctrl = helper.random_port()
            _args.socket_out = SocketType.PUSH_CONNECT
            _args.socket_in = SocketType.DEALER_CONNECT

            _args.host_in = BasePod._fill_in_host(
                bind_args=head_args, connect_args=_args
            )
            _args.host_out = BasePod._fill_in_host(
                bind_args=tail_args, connect_args=_args
            )
            result.append(_args)
        return result

    def rolling_update(self):
        """
        Update all pods of this compound pod.
        """
        for i in range(len(self.replica_list)):
            replica = self.replica_list[i]
            replica.close()
            _args = self.all_args['replicas'][i]
            _args.noblock_on_start = False
            new_replica = Pod(_args)
            self.enter_context(new_replica)
            self.replica_list[i] = new_replica
