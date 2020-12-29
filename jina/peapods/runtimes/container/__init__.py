import argparse
import os
import sys
import time
from pathlib import Path

from ..zmq.base import ZMQRuntime
from ...zmq import Zmqlet
from ....helper import ArgNamespace, is_valid_local_config_source
from ....logging import JinaLogger


class ContainerRuntime(ZMQRuntime):

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        self._set_network_for_dind_linux()

    def setup(self):
        self._docker_run()
        while self._is_container_alive and not self.is_ready:
            time.sleep(1)
        # two cases to reach here: 1. is_ready, 2. container is dead
        if not self._is_container_alive:
            raise Exception('the container fails to start, check the arguments or entrypoint')

    def teardown(self):
        self._container.stop()

    def run_forever(self):
        with JinaLogger('🐳', **vars(self.args)) as logger:
            for line in self._container.logs(stream=True):
                logger.info(line.strip().decode())

    def _set_network_for_dind_linux(self):
        import docker
        # recompute the control_addr, do not assign client, since this would be an expensive object to
        # copy in the new process generated
        client = docker.from_env()

        # Related to potential docker-in-docker communication. If `ContainerPea` lives already inside a container.
        # it will need to communicate using the `bridge` network.
        self._net_mode = None
        if sys.platform in ('linux', 'linux2'):
            self._net_mode = 'host'
            try:
                bridge_network = client.networks.get('bridge')
                if bridge_network:
                    self.ctrl_addr, _ = Zmqlet.get_ctrl_address(
                        bridge_network.attrs['IPAM']['Config'][0]['Gateway'],
                        self.args.port_ctrl,
                        self.args.ctrl_with_ipc)
            except Exception as ex:
                self.logger.warning(f'Unable to set control address from "bridge" network: {ex!r}'
                                    f' Control address set to {self.ctrl_addr}')
        client.close()

    def _docker_run(self):
        # important to notice, that client is not assigned as instance member to avoid potential
        # heavy copy into new process memory space
        import docker
        client = docker.from_env()

        # the image arg should be ignored otherwise it keeps using ContainerPea in the container
        # basically all args in BasePea-docker arg group should be ignored.
        # this prevent setting containerPea twice
        from ....parsers import set_pea_parser
        non_defaults = ArgNamespace.get_non_defaults_args(self.args, set_pea_parser(),
                                                          taboo={'uses', 'entrypoint', 'volumes', 'pull_latest'})

        if self.args.pull_latest:
            self.logger.warning(f'pulling {self.args.uses}, this could take a while. if you encounter '
                                f'timeout error due to pulling takes to long, then please set '
                                f'"timeout-ready" to a larger value.')
            client.images.pull(self.args.uses)

        _volumes = {}
        if self.args.uses_internal:
            if os.path.exists(self.args.uses_internal):
                # external YAML config, need to be volumed into the container
                # uses takes value from uses_internal
                non_defaults['uses'] = '/' + os.path.basename(self.args.uses_internal)
                _volumes[os.path.abspath(self.args.uses_internal)] = {'bind': non_defaults['uses'], 'mode': 'ro'}
            elif not is_valid_local_config_source(self.args.uses_internal):
                raise FileNotFoundError(
                    f'"uses_internal" {self.args.uses_internal} is not like a path, please check it')
        if self.args.volumes:
            for p in self.args.volumes:
                Path(os.path.abspath(p)).mkdir(parents=True, exist_ok=True)
                _p = '/' + os.path.basename(p)
                _volumes[os.path.abspath(p)] = {'bind': _p, 'mode': 'rw'}

        _expose_port = [self.args.port_ctrl]
        if self.args.socket_in.is_bind:
            _expose_port.append(self.args.port_in)
        if self.args.socket_out.is_bind:
            _expose_port.append(self.args.port_out)

        _args = ArgNamespace.kwargs2list(non_defaults)
        ports = {f'{v}/tcp': v for v in _expose_port} if not self._net_mode else None
        self._container = client.containers.run(self.args.uses, _args,
                                                detach=True,
                                                auto_remove=True,
                                                ports=ports,
                                                name=self.name,
                                                volumes=_volumes,
                                                network_mode=self._net_mode,
                                                entrypoint=self.args.entrypoint)
        client.close()

    @property
    def _is_container_alive(self) -> bool:
        import docker.errors
        try:
            self._container.reload()
        except docker.errors.NotFound:
            return False
        return True
