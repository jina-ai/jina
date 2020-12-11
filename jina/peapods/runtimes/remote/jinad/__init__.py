from argparse import Namespace
from typing import Union, Dict, Optional

from jina.peapods.runtimes.remote.jinad.api import PeaAPI
from jina.peapods.runtimes.remote import RemoteRunTime
from jina.helper import cached_property, namespace_to_dict, colored, typename
from .api import get_jinad_api


class RemoteJinaDRunTime(RemoteRunTime):
    """REST based Pea for remote Pea management
    """
    def __init__(self, args: Union['Namespace', Dict], kind: str):
        super().__init__(args, kind=kind)
        if isinstance(self.args, Namespace):
            self.ctrl_timeout = self.args.timeout_ctrl
        self.api = get_jinad_api(kind=self.kind, host=self.args.host, port=self.args.port_expose, logger=self.logger)

    @cached_property
    def remote_id(self) -> str:
        return self.spawn_remote()

    def spawn_remote(self, **kwargs) -> Optional[str]:
        if self.api.is_alive:
            pea_args = namespace_to_dict(self.args)
            if self.api.upload(pea_args, **kwargs):
                return self.api.create(pea_args, **kwargs)

    def _monitor_remote(self):
        if self.remote_id:
            self.logger.success(f'created remote {self.api.kind} with id {colored(self.remote_id, "cyan")}')
            self.set_ready()
            self.api.log(self.remote_id, self.is_shutdown)
        else:
            self.logger.error(f'fail to create {typename(self)} remotely')
