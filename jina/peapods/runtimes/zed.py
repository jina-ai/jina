from jina.peapods.runtimes import BaseRuntime
import argparse
import os
import time
from collections import defaultdict
from contextlib import ExitStack
from multiprocessing.synchronize import Event
from typing import Dict, Optional, Union, List

import zmq

from ..zmq import ZmqStreamlet
from ... import Message
from ... import Request
from ...enums import PeaRoleType, SkipOnErrorType
from ...excepts import RequestLoopEnd, NoExplicitMessage, ExecutorFailToLoad, MemoryOverHighWatermark, DriverError, \
    ChainedPodException, BadConfigSource
from ...executors import BaseExecutor
from ...logging import JinaLogger
from ...logging.profile import used_memory, TimeDict
from ...proto import jina_pb2

class ZEDRuntime(BaseRuntime):
    def run_forever(self):
        pass

    def cancel(self):
        pass

    def setup(self):
        self.last_active_time = time.perf_counter()
        self.last_dump_time = time.perf_counter()

        self._timer = TimeDict()

        self._request = None
        self._message = None

        # all pending messages collected so far, key is the request id
        self._pending_msgs = defaultdict(list)  # type: Dict[str, List['Message']]
        self._partial_requests = None
        self._partial_messages = None

    #: Private methods required by :meth:`setup`

    def _load_executor(self):
        """Load the executor to this BasePea, specified by ``uses`` CLI argument.
        """
        try:
            try:
                self.executor = BaseExecutor.load_config(self.args.uses,
                                                         separated_workspace=self.args.separated_workspace,
                                                         pea_id=self.args.pea_id,
                                                         read_only=self.args.read_only)
            except BadConfigSource:
                # retry loading but with "uses_internal" as the source
                self.executor = BaseExecutor.load_config(self.args.uses_internal,
                                                         separated_workspace=self.args.separated_workspace,
                                                         pea_id=self.args.pea_id,
                                                         read_only=self.args.read_only)
            self.executor.attach(pea=self)
        except FileNotFoundError as ex:
            self.logger.error(f'fail to load file dependency: {repr(ex)}')
            raise ExecutorFailToLoad from ex
        except Exception as ex:
            raise ExecutorFailToLoad from ex

    #: Private methods required by :meth:`teardown`

    def _save_executor(self):
        """Save the contained executor according to the `dump_interval` parameter
        """
        if (time.perf_counter() - self.last_dump_time) > self.args.dump_interval > 0:
            self.executor.save()
            self.last_dump_time = time.perf_counter()
            if hasattr(self, 'zmqlet'):
                self.zmqlet.print_stats()

    #: Some class-specific properties

    @property
    def is_idle(self) -> bool:
        """Return ``True`` when current time is ``max_idle_time`` seconds late than the last active time"""
        return (time.perf_counter() - self.last_active_time) > self.args.max_idle_time

    @property
    def request(self) -> 'Request':
        """Get the current request body inside the protobuf message"""
        return self._request

    @property
    def message(self) -> 'Message':
        """Get the current protobuf message to be processed"""
        return self._message

    @property
    def request_type(self) -> str:
        """Get the type of message being processed"""
        return self._message.envelope.request_type

    @property
    def expect_parts(self) -> int:
        """The expected number of partial messages before trigger :meth:`handle` """
        return self.args.num_part if self.message.is_data_request else 1

    @property
    def partial_requests(self) -> List['Request']:
        """The collected partial requests under the current ``request_id`` """
        return self._partial_requests

    @property
    def partial_messages(self) -> List['Message']:
        """The collected partial messages under the current ``request_id`` """
        return self._partial_messages