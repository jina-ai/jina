import argparse
from abc import ABC

from ..base import BaseRuntime


# TODO(Joan) Remove ZMQRuntime
class ZMQRuntime(BaseRuntime, ABC):
    """Runtime procedure leveraging ZMQ."""

    def __init__(self, args: 'argparse.Namespace', ctrl_addr: str, **kwargs):
        super().__init__(args, **kwargs)
        self.ctrl_addr = ctrl_addr
