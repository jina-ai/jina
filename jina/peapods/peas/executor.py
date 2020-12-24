import argparse
import time
from collections import defaultdict
from typing import Dict, List

from .zmq import ZMQControlPea
from ... import Message
from ... import Request


class ExecutorPea(ZMQControlPea):
    def __init__(self, args: 'argparse.Namespace'):
        """ Create a new :class:`BasePea` object

        :param args: the arguments received from the CLI
        """
        super().__init__(args)

        self.last_active_time = time.perf_counter()
        self.last_dump_time = time.perf_counter()

        self._request = None
        self._message = None

        # all pending messages collected so far, key is the request id
        self._pending_msgs = defaultdict(list)  # type: Dict[str, List['Message']]
        self._partial_requests = None
        self._partial_messages = None

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
