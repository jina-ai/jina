import copy
from argparse import Namespace
from itertools import cycle
from typing import Optional, Dict, List, Union, Set

from .. import BasePod
from .. import Pea
from .. import Pod
from ... import helper
from ...enums import PollingType, SocketType
from ...helper import random_identity


class CompoundPod(BasePod):
    """A CompoundPod is a immutable set of pods, which run in parallel.
    A CompoundPod is an abstraction using a composable pattern to abstract the usage of parallel Pods that act as replicas.

    CompoundPod will make sure to add a `HeadPea` and a `TailPea` to serve as routing/merging pattern for the different Pod replicas

    :param args: pod arguments parsed from the CLI. These arguments will be used for each of the replicas
    :param needs: pod names of preceding pods, the output of these pods are going into the input of this pod
    """

    head_args = None
    tail_args = None

    def __init__(
        self, args: Union['Namespace', Dict], needs: Optional[Set[str]] = None
    ):
        super().__init__(args, needs)
        self.replicas = []  # type: List['Pod']
        # we will see how to have `CompoundPods` in remote later when we add tests for it
        self.is_head_router = True
        self.is_tail_router = True
        self.head_args = BasePod._copy_to_head_args(args, PollingType.ANY)
        self.tail_args = BasePod._copy_to_tail_args(args, PollingType.ANY)
        cargs = copy.copy(args)
        self.replicas_args = self._set_replica_args(
            cargs, self.head_args, self.tail_args
        )

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

    def _parse_pod_args(self, args: Namespace) -> List[Namespace]:
        return self._set_replica_args(
            args,
            head_args=self.head_args,
            tail_args=self.tail_args,
        )

    @property
    def num_peas(self) -> int:
        """
        Get the number of running :class:`Pod`

        :return: total number of peas including head and tail
        """
        return sum([replica.num_peas for replica in self.replicas]) + 2

    def __eq__(self, other: 'CompoundPod'):
        return self.num_peas == other.num_peas and self.name == other.name

    def _enter_pea(self, pea: 'Pea') -> None:
        self.enter_context(pea)

    def start(self) -> 'CompoundPod':
        """
        Start to run all :class:`Pod` and :class:`Pea` in this CompoundPod.

        :return: started CompoundPod

        .. note::
            If one of the :class:`Pod` fails to start, make sure that all of them
            are properly closed.
        """
        if getattr(self.args, 'noblock_on_start', False):
            head_args = self.head_args
            head_args.noblock_on_start = True
            self.head_pea = Pea(head_args)
            self._enter_pea(self.head_pea)
            for _args in self.replicas_args:
                _args.noblock_on_start = True
                _args.polling = PollingType.ALL
                self._enter_replica(Pod(_args))
            tail_args = self.tail_args
            tail_args.noblock_on_start = True
            self.tail_pea = Pea(tail_args)
            self._enter_pea(self.tail_pea)
            # now rely on higher level to call `wait_start_success`
            return self
        else:
            try:
                head_args = self.head_args
                self.head_pea = Pea(head_args)
                self._enter_pea(self.head_pea)
                for _args in self.replicas_args:
                    _args.polling = PollingType.ALL
                    self._enter_replica(Pod(_args))
                tail_args = self.tail_args
                self.tail_pea = Pea(tail_args)
                self._enter_pea(self.tail_pea)
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
            self.head_pea.wait_start_success()
            self.tail_pea.wait_start_success()
            for p in self.replicas:
                p.wait_start_success()
        except:
            self.close()
            raise

    def _enter_replica(self, replica: 'Pod') -> None:
        self.replicas.append(replica)
        self.enter_context(replica)

    def join(self):
        """Wait until all pods and peas exit."""
        try:
            if getattr(self, 'head_pea', None):
                self.head_pea.join()
            if getattr(self, 'head_pea', None):
                self.tail_pea.join()
            for p in self.replicas:
                p.join()
        except KeyboardInterrupt:
            pass
        finally:
            self.replicas.clear()

    @property
    def is_ready(self) -> bool:
        """
        Checks if Pod is read.
        :return: true if the peas and pods are ready to serve requests

        .. note::
            A Pod is ready when all the Peas it contains are ready
        """
        return all(
            [p.is_ready.is_set() for p in [self.head_pea, self.tail_pea]]
            + [p.is_ready for p in self.replicas]
        )

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

    def rolling_update(self, dump_path: Optional[str] = None):
        """Reload all Pods of this Compound Pod.

        :param dump_path: the dump from which to read the data
        """
        try:
            for i in range(len(self.replicas)):
                replica = self.replicas[i]
                replica.close()
                _args = self.replicas_args[i]
                _args.noblock_on_start = False
                # TODO better way to pass args to the new Pod
                _args.dump_path = dump_path
                new_replica = Pod(_args)
                self.enter_context(new_replica)
                self.replicas[i] = new_replica
                # TODO might be required in order to allow time for the Replica to come online
                # before taking down the next
        except:
            raise
