__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from argparse import Namespace
from typing import Dict, Union, Type, Optional, Any

from .jinad import PeaAPI, PodAPI
from .pea import BasePea
from ..helper import colored, cached_property


def namespace_to_dict(args: Union[Dict[str, 'Namespace'], 'Namespace']) -> Dict[str, Any]:
    """ helper function to convert argparse.Namespace to json to be uploaded via REST """
    if isinstance(args, Namespace):
        return vars(args)
    elif isinstance(args, dict):
        pea_args = {}
        for k, v in args.items():
            if isinstance(v, Namespace):
                pea_args[k] = vars(v)
            elif isinstance(v, list):
                pea_args[k] = [vars(_) for _ in v]
            else:
                pea_args[k] = v
        return pea_args


class RemotePea(BasePea):
    """REST based Pea for remote Pea management

    # TODO: This shouldn't inherit BasePea, Needs to change to a runtime
    """

    APIClass = PeaAPI  # type: Type['JinadAPI']

    @cached_property
    def remote_id(self) -> str:
        return self.spawn_remote(host=self.args.host, port=self.args.port_expose)

    def spawn_remote(self, host: str, port: int, **kwargs) -> Optional[str]:
        self.api = self.APIClass(host, port, self.logger, **kwargs)

        if self.api.is_alive:
            pea_args = namespace_to_dict(self.args)
            if self.api.upload(pea_args, **kwargs):
                return self.api.create(pea_args, **kwargs)

    def loop_body(self):
        if self.remote_id:
            self.logger.success(f'created remote pea with id {colored(self.remote_id, "cyan")}')
            self.set_ready()
            self.api.log(self.remote_id)
        else:
            self.logger.error(f'fail to create {self.__class__.__name__} remotely')
            self.is_shutdown.set()

    def loop_teardown(self):
        if hasattr(self, 'api') and self.api.is_alive and self.remote_id:
            self.api.delete(self.remote_id)


class RemotePod(RemotePea):
    """REST based pod to be used while invoking remote Pod
    """

    APIClass = PodAPI  # type: Type['JinadAPI']

    def spawn_remote(self, host: str, port: int, pod_type: str = 'cli', **kwargs) -> Optional[str]:
        return super().spawn_remote(host, port, pod_type=pod_type)

    # TODO: this is a hack, as close runs in a separate process when triggered in cli
    # This should be tackled when moving from BasePea inheritance
    def close(self):
        pass


class RemoteMutablePod(RemotePod):
    """REST based Mutable pod to be used while invoking remote Pod via Flow API
    """

    def spawn_remote(self, host: str, port: int, pod_type: str = 'flow', **kwargs) -> Optional[str]:
        return super().spawn_remote(host, port, pod_type=pod_type)
