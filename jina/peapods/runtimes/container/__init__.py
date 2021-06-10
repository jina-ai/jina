import argparse
import os
import sys
import time
import warnings
from pathlib import Path

from ..zmq.base import ZMQRuntime
from ...zmq import Zmqlet
from ....excepts import BadImageNameError
from ....helper import ArgNamespace, is_valid_local_config_source, slugify
from ....jaml.helper import complete_path


class ContainerRuntime(ZMQRuntime):
    """Runtime procedure for container."""

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)
        self._set_network_for_dind_linux()

    def setup(self):
        """Run the container."""
        self._docker_run()
        while self._is_container_alive and not self.is_ready:
            time.sleep(1)
        # two cases to reach here: 1. is_ready, 2. container is dead
        if not self._is_container_alive:
            # replay it to see the log
            self._docker_run(replay=True)
            raise Exception(
                'the container fails to start, check the arguments or entrypoint'
            )

    def teardown(self):
        """Stop the container."""
        self._container.stop()
        super().teardown()

    def _stream_logs(self):
        for line in self._container.logs(stream=True):
            self.logger.info(line.strip().decode())

    def run_forever(self):
        """Stream the logs while running."""
        self._stream_logs()

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
                        self.args.ctrl_with_ipc,
                    )
            except Exception as ex:
                self.logger.warning(
                    f'Unable to set control address from "bridge" network: {ex!r}'
                    f' Control address set to {self.ctrl_addr}'
                )
        client.close()

    def _docker_run(self, replay: bool = False):
        # important to notice, that client is not assigned as instance member to avoid potential
        # heavy copy into new process memory space
        import docker

        client = docker.from_env()

        if self.args.uses.startswith('docker://'):
            uses_img = self.args.uses.replace('docker://', '')
            self.logger.info(f'will use Docker image: {uses_img}')
        else:
            warnings.warn(
                f'you are using legacy image format {self.args.uses}, this may create some ambiguity. '
                f'please use the new format: "--uses docker://{self.args.uses}"'
            )
            uses_img = self.args.uses

        # the image arg should be ignored otherwise it keeps using ContainerPea in the container
        # basically all args in BasePea-docker arg group should be ignored.
        # this prevent setting containerPea twice
        from ....parsers import set_pea_parser

        non_defaults = ArgNamespace.get_non_defaults_args(
            self.args,
            set_pea_parser(),
            taboo={
                'uses',
                'entrypoint',
                'volumes',
                'pull_latest',
                'runtime_cls',
                'docker_kwargs',
            },
        )

        img_not_found = False

        try:
            client.images.get(uses_img)
        except docker.errors.ImageNotFound:
            self.logger.error(f'can not find local image: {uses_img}')
            img_not_found = True

        if self.args.pull_latest or img_not_found:
            self.logger.warning(
                f'pulling {uses_img}, this could take a while. if you encounter '
                f'timeout error due to pulling takes to long, then please set '
                f'"timeout-ready" to a larger value.'
            )
            try:
                client.images.pull(uses_img)
                img_not_found = False
            except docker.errors.NotFound:
                img_not_found = True
                self.logger.error(f'can not find remote image: {uses_img}')

        if img_not_found:
            raise BadImageNameError(
                f'image: {uses_img} can not be found local & remote.'
            )

        _volumes = {}
        if self.args.uses_internal:
            full_path = None
            try:
                full_path = complete_path(self.args.uses_internal)
            except FileNotFoundError:
                pass
            if full_path and os.path.exists(full_path):
                # external YAML config, need to be volumed into the container
                # uses takes value from uses_internal
                non_defaults['uses'] = '/' + os.path.basename(full_path)
                _volumes[full_path] = {'bind': non_defaults['uses'], 'mode': 'ro'}
            elif not is_valid_local_config_source(self.args.uses_internal):
                raise FileNotFoundError(
                    f'"uses_internal" {self.args.uses_internal} is not like a path, please check it'
                )
        if self.args.volumes:
            for p in self.args.volumes:
                paths = p.split(':')
                local_path = paths[0]
                Path(os.path.abspath(local_path)).mkdir(parents=True, exist_ok=True)
                if len(paths) == 2:
                    container_path = paths[1]
                else:
                    container_path = '/' + os.path.basename(p)
                _volumes[os.path.abspath(local_path)] = {
                    'bind': container_path,
                    'mode': 'rw',
                }

        _expose_port = [self.args.port_ctrl]
        if self.args.socket_in.is_bind:
            _expose_port.append(self.args.port_in)
        if self.args.socket_out.is_bind:
            _expose_port.append(self.args.port_out)

        _args = ArgNamespace.kwargs2list(non_defaults)
        ports = {f'{v}/tcp': v for v in _expose_port} if not self._net_mode else None

        docker_kwargs = self.args.docker_kwargs or {}
        self._container = client.containers.run(
            uses_img,
            _args,
            detach=True,
            auto_remove=True,
            ports=ports,
            name=slugify(self.name),
            volumes=_volumes,
            network_mode=self._net_mode,
            entrypoint=self.args.entrypoint,
            **docker_kwargs,
        )

        if replay:
            # when replay is on, it means last time it fails to start
            # therefore we know the loop below wont block the main process
            self._stream_logs()

        client.close()

    @property
    def _is_container_alive(self) -> bool:
        import docker.errors

        try:
            self._container.reload()
        except docker.errors.NotFound:
            return False
        return True
