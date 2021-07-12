import argparse
import os
import sys
import time
import warnings
from pathlib import Path
from platform import uname

from ..zmq.base import ZMQRuntime
from ...zmq import Zmqlet
from .... import __docker_host__
from ....excepts import BadImageNameError, DockerVersionError
from ...zmq import send_ctrl_message
from ....helper import ArgNamespace, slugify


class ContainerRuntime(ZMQRuntime):
    """Runtime procedure for container."""

    def __init__(self, args: 'argparse.Namespace', ctrl_addr: str, **kwargs):
        super().__init__(args, ctrl_addr, **kwargs)
        self._set_network_for_dind_linux()
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
        self.is_ready_event.set()
        self._stream_logs()

    def _set_network_for_dind_linux(self):
        import docker

        # recompute the control_addr, do not assign client, since this would be an expensive object to
        # copy in the new process generated
        client = docker.from_env()

        # Related to potential docker-in-docker communication. If `ContainerPea` lives already inside a container.
        # it will need to communicate using the `bridge` network.
        self._net_mode = None

        # In WSL, we need to set ports explicitly
        if sys.platform in ('linux', 'linux2') and 'microsoft' not in uname().release:
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

    @staticmethod
    def _get_gpu_device_requests(gpu_args):
        import docker

        _gpus = {
            'count': 0,
            'capabilities': ['gpu'],
            'device': [],
            'driver': '',
        }
        for gpu_arg in gpu_args.split(','):
            if gpu_arg == 'all':
                _gpus['count'] = -1
            if gpu_arg.isdigit():
                _gpus['count'] = int(gpu_arg)
            if '=' in gpu_arg:
                gpu_arg_key, gpu_arg_value = gpu_arg.split('=')
                if gpu_arg_key in _gpus.keys():
                    if isinstance(_gpus[gpu_arg_key], list):
                        _gpus[gpu_arg_key].append(gpu_arg_value)
                    else:
                        _gpus[gpu_arg_key] = gpu_arg_value
        device_requests = [
            docker.types.DeviceRequest(
                count=_gpus['count'],
                driver=_gpus['driver'],
                device_ids=_gpus['device'],
                capabilities=[_gpus['capabilities']],
            )
        ]
        return device_requests

    def _docker_run(self, replay: bool = False):
        # important to notice, that client is not assigned as instance member to avoid potential
        # heavy copy into new process memory space
        import docker

        client = docker.from_env()

        docker_version = client.version().get('Version')
        if not docker_version:
            raise DockerVersionError('docker version can not be resolved')

        docker_version = tuple(docker_version.split('.'))
        # docker daemon versions below 20.0x do not support "host.docker.internal:host-gateway"
        if docker_version < ('20',):
            raise DockerVersionError(
                f'docker version {".".join(docker_version)} is below 20.0.0 and does not '
                f'support "host.docker.internal:host-gateway" : https://github.com/docker/cli/issues/2664'
            )

        if self.args.uses.startswith('docker://'):
            uses_img = self.args.uses.replace('docker://', '')
            self.logger.debug(f'will use Docker image: {uses_img}')
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

        self.args.runs_in_docker = True
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
                'gpus',
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

        device_requests = []
        if self.args.gpus:
            device_requests = self._get_gpu_device_requests(self.args.gpus)
            del self.args.gpus

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
            extra_hosts={__docker_host__: 'host-gateway'},
            device_requests=device_requests,
            **docker_kwargs,
        )

        if replay:
            # when replay is on, it means last time it fails to start
            # therefore we know the loop below wont block the main process
            self._stream_logs()

        client.close()

    @property
    def status(self):
        """
        Send get status control message.

        :return: control message.
        """
        return send_ctrl_message(
            self.ctrl_addr, 'STATUS', timeout=self.args.timeout_ctrl
        )

    @property
    def is_ready(self) -> bool:
        """
        Check if status is ready.

        :return: True if status is ready else False.
        """
        status = self.status
        return status and status.is_ready

    @property
    def _is_container_alive(self) -> bool:
        import docker.errors

        try:
            self._container.reload()
        except docker.errors.NotFound:
            return False
        return True
