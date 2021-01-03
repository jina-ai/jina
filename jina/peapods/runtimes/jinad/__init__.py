import argparse
from typing import Union, Dict, Optional

from .api import PeaJinadAPI, get_jinad_api
from ..zmq.base import ZMQManyRuntime
from ....helper import cached_property, ArgNamespace, colored


class JinadRuntime(ZMQManyRuntime):

    def __init__(self, args: Union['argparse.Namespace', Dict]):
        super().__init__(args)
        self.api = get_jinad_api(kind=self.remote_type, host=self.host, port=self.port_expose, logger=self.logger)

    def setup(self):
        if self._remote_id:
            self.logger.success(f'created remote {self.api.kind} with id {colored(self._remote_id, "cyan")}')

    def run_forever(self):
        self.api.log(self._remote_id, None)

    @cached_property
    def _remote_id(self) -> Optional[str]:
        if self.api.is_alive:
            args = ArgNamespace.flatten_to_dict(self.args)
            if self.api.upload(args):
                return self.api.create(args)
