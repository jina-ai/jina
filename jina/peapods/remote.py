__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from pathlib import Path
from argparse import Namespace
from contextlib import ExitStack
from typing import Callable, Dict, List, Tuple, Union

import ruamel.yaml

from .pea import BasePea
from .jinad import PeaAPI, PodAPI
from ..helper import colored


def namespace_to_dict(args: Union[Dict, Namespace]) -> Dict:
    """ helper function to convert argparse.Namespace to json to be uploaded via REST """
    if isinstance(args, Dict):
        pea_args = {}
        for k, v in args.items():
            if v is None:
                pea_args[k] = None
            if isinstance(v, Namespace):
                pea_args[k] = vars(v)
            if isinstance(v, list):
                pea_args[k] = []
                pea_args[k].extend([vars(_) for _ in v])
        return pea_args

    if isinstance(args, Namespace):
        return vars(args)


class RemotePea(BasePea):
    """REST based Pea for remote Pea management """
    # TODO: This shouldn't inherit BasePea, Needs to change to a runtime
    def is_alive(self):
        if not self.api.is_alive():
            self.logger.error('couldn\'t connect to the remote jinad')
            self.is_shutdown.set()
            return False
        else:
            self.logger.success('connected to the remote jinad')
            return True

    def configure_api(self, kind: str, host: str, port: int):
        self.logger.info(f'got host {host} and port {port} for remote jinad {kind}')
        self.api = PeaAPI(host, port, self.logger) if kind == 'pea' else PodAPI(host, port, self.logger)

    def loop_body(self):
        self.configure_api(kind='pea',
                           host=self.args.host,
                           port=self.args.port_expose)
        if self.is_alive():
            pea_args = namespace_to_dict(self.args)
            self.api.upload(pea_args=pea_args)
            self.pea_id = self.api.create(pea_args=pea_args)
            if not self.pea_id:
                self.logger.error('remote pea creation failed')
                self.is_shutdown.set()
                return
            self.logger.success(f'created remote pea with id {colored(self.pea_id, "cyan")}')
            self.set_ready()
            self.api.log(pea_id=self.pea_id)

    def loop_teardown(self):
        if self.is_alive():
            status = self.api.delete(pea_id=self.pea_id)
            if status:
                self.logger.success(f'successfully closed pea with id {colored(self.pea_id, "cyan")}')
            else:
                self.logger.error('remote pea close failed')


class RemotePod(RemotePea):

    def _create_and_log(self, pod_type):
        if self.is_alive():
            pea_args = namespace_to_dict(self.args)
            self.api.upload(pea_args=pea_args)
            self.pod_id = self.api.create(pea_args=pea_args,
                                          pod_type=pod_type)
            if not self.pod_id:
                self.logger.error('remote pod creation failed')
                self.is_shutdown.set()
                return
            self.logger.success(f'created remote pod with id {colored(self.pod_id, "cyan")}')
            self.set_ready()
            self.api.log(pod_id=self.pod_id)

    def loop_body(self):
        self.configure_api(kind='pod',
                           host=self.args.host,
                           port=self.args.port_expose)
        self._create_and_log(pod_type='cli')

    def _delete(self):
        if self.is_alive():
            status = self.api.delete(pod_id=self.pod_id)
            if status:
                self.logger.success(f'successfully closed pod with id {colored(self.pod_id, "cyan")}')
            else:
                self.logger.error('remote pod close failed')

    def loop_teardown(self):
        self._delete()

    # TODO: this is a hack, as close runs in a separate process when triggered in cli
    # This should be tackled when moving from BasePea inheritance
    def close(self):
        pass


class RemoteMutablePod(RemotePod):
    """REST based Mutable pod to be used while invoking remote Pod via Flow API

    """
    def loop_body(self):
        try:
            self.configure_api(kind='pod',
                               host=self.args['peas'][0].host,
                               port=self.args['peas'][0].port_expose)
        except (KeyError, AttributeError):
            self.logger.error('unable to fetch host & port of remote pod\'s REST interface')
            self.is_shutdown.set()
        self._create_and_log(pod_type='flow')

    def loop_teardown(self):
        pass

    def close(self):
        self._delete()
