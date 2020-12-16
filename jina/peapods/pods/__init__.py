__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

import argparse
import time
from argparse import Namespace
from contextlib import ExitStack
from threading import Thread
from typing import Optional, Dict, List, Union

from .helper import _set_peas_args, _set_after_to_pass, _copy_to_head_args, _copy_to_tail_args, _fill_in_host
from .. import Runtime
from ..peas import BasePea
from ..peas.headtail import HeadPea, TailPea
from ...enums import *


class BasePod(ExitStack):
    """A BasePod is a immutable set of peas, which run in parallel. They share the same input and output socket.
    Internally, the peas can run with the process/thread backend. They can be also run in their own containers
    """

    def __init__(self, args: Union['argparse.Namespace', Dict]):
        """

        :param args: arguments parsed from the CLI
        """
        super().__init__()
        self.runtimes = []
        self.is_head_router = False
        self.is_tail_router = False
        self.deducted_head = None
        self.deducted_tail = None
        self._args = args
        self.peas_args = self._parse_args(args)

    @property
    def is_singleton(self) -> bool:
        """Return if the Pod contains only a single Pea """
        return not (self.is_head_router or self.is_tail_router)

    @property
    def is_idle(self) -> bool:
        """A Pod is idle when all its peas are idle, see also :attr:`jina.peapods.pea.Pea.is_idle`.
        """
        return all(runtime.is_idle for runtime in self.runtimes if runtime.is_ready_event.is_set())

    def close_if_idle(self):
        """Check every second if the pod is in idle, if yes, then close the pod"""
        while True:
            if self.is_idle:
                self.close()
            time.sleep(1)

    @property
    def name(self) -> str:
        """The name of this :class:`BasePod`. """
        return self.first_pea_args.name

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
        elif getattr(args, 'uses_before', None) or getattr(args, 'uses_after', None):
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
        return self.peas_args['peas'] + (
            [self.peas_args['head']] if self.peas_args['head'] else []) + (
                   [self.peas_args['tail']] if self.peas_args['tail'] else [])

    @property
    def num_peas(self) -> int:
        """Get the number of running :class:`BasePea`"""
        return len(self.runtimes)

    def __eq__(self, other: 'BasePod'):
        return self.num_peas == other.num_peas and self.name == other.name

    def set_runtime(self, runtime: str):
        """Set the parallel runtime of this BasePod.

        :param runtime: possible values: process, thread
        """
        for s in self.all_args:
            s.runtime = runtime
            # for thread and process backend which runs locally, host_in and host_out should not be set
            # s.host_in = __default_host__
            # s.host_out = __default_host__

    def start_sentinels(self) -> None:
        self.sentinel_threads = []
        if isinstance(self._args, argparse.Namespace) and getattr(self._args, 'shutdown_idle', False):
            self.sentinel_threads.append(Thread(target=self.close_if_idle,
                                                name='sentinel-shutdown-idle',
                                                daemon=True))
        for t in self.sentinel_threads:
            t.start()

    def start(self) -> 'BasePod':
        """Start to run all Peas in this BasePod.

        Remember to close the BasePod with :meth:`close`.

        Note that this method has a timeout of ``timeout_ready`` set in CLI,
        which is inherited from :class:`jina.peapods.peas.BasePea`
        """
        # start head and tail
        if self.peas_args['head']:
            p = Runtime(self.peas_args['head'], pea_cls=HeadPea, allow_remote=False)
            self.runtimes.append(p)
            self.enter_context(p)

        if self.peas_args['tail']:
            p = Runtime(self.peas_args['tail'], pea_cls=TailPea, allow_remote=False)
            self.runtimes.append(p)
            self.enter_context(p)

        # start real peas and accumulate the storage id
        if len(self.peas_args['peas']) > 1:
            start_rep_id = 1
            role = PeaRoleType.PARALLEL
        else:
            start_rep_id = 0
            role = PeaRoleType.SINGLETON
        for idx, _args in enumerate(self.peas_args['peas'], start=start_rep_id):
            _args.pea_id = idx
            _args.role = role
            p = Runtime(_args, pea_cls=BasePea, allow_remote=False)
            self.runtimes.append(p)
            self.enter_context(p)

        self.start_sentinels()
        return self

    @property
    def is_shutdown(self) -> bool:
        return all(not runtime.is_ready_event.is_set() for runtime in self.runtimes)

    def __enter__(self) -> 'BasePod':
        return self.start()

    @property
    def status(self) -> List:
        """The status of a BasePod is the list of status of all its Peas """
        return [runtime.status for runtime in self.runtimes]

    def is_ready(self) -> bool:
        """Wait till the ready signal of this BasePod.

        The pod is ready only when all the contained Peas returns is_ready_event
        """
        for runtime in self.runtimes:
            runtime.is_ready_event.wait()
        return True

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        super().__exit__(exc_type, exc_val, exc_tb)

    def join(self):
        """Wait until all peas exit"""
        try:
            for runtime in self.runtimes:
                runtime.join()
        except KeyboardInterrupt:
            pass
        finally:
            self.runtimes.clear()
