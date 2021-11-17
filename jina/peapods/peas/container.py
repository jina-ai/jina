import os
import argparse
import time

import multiprocessing
import threading

from typing import TYPE_CHECKING, Union
import asyncio

from . import BasePea
from .helper import _get_worker
from .container_helper import get_gpu_device_requests, get_docker_network
from ...enums import RuntimeBackendType
from ... import __docker_host__
from ...logging.logger import JinaLogger
from ..runtimes.asyncio import AsyncNewLoopRuntime

if TYPE_CHECKING:
    from docker.models.containers import Container


def run(
    args: 'argparse.Namespace',
    name: str,
    container_id: str,
    runtime_ctrl_address: str,
    is_started: Union['multiprocessing.Event', 'threading.Event'],
    is_shutdown: Union['multiprocessing.Event', 'threading.Event'],
    is_ready: Union['multiprocessing.Event', 'threading.Event'],
):
    """Method to be run in a process that stream logs from a Container

    This method is the target for the Pea's `thread` or `process`

    .. note::
        :meth:`run` is running in subprocess/thread, the exception can not be propagated to the main process.
        Hence, please do not raise any exception here.

    .. note::
        Please note that env variables are process-specific. Subprocess inherits envs from
        the main process. But Subprocess's envs do NOT affect the main process. It does NOT
        mess up user local system envs.

    :param args: namespace args from the Pea
    :param name: name of the Pea to have proper logging
    :param container_id: the id of the container from which to stream logs
    :param runtime_ctrl_address: the control address of the runtime living in the container
    :param is_started: concurrency event to communicate runtime is properly started. Used for better logging
    :param is_shutdown: concurrency event to communicate runtime is terminated
    :param is_ready: concurrency event to communicate runtime is ready to receive messages
    """
    import docker

    logger = JinaLogger(name, **vars(args))
    _fail_to_start = asyncio.Event()

    def _is_ready():
        return AsyncNewLoopRuntime.is_ready(runtime_ctrl_address)

    def _is_container_alive(container: 'Container') -> bool:
        import docker.errors

        try:
            container.reload()
        except docker.errors.NotFound:
            return False
        return True

    async def _check_readiness(container: 'Container'):
        while _is_container_alive(container) and not _is_ready():
            await asyncio.sleep(0.1)
        if _is_container_alive(container):
            is_started.set()
            is_ready.set()
        else:
            _fail_to_start.set()

    async def _stream_starting_logs(container: 'Container'):
        for line in container.logs(stream=True):
            if not is_started.is_set() and not _fail_to_start.is_set():
                await asyncio.sleep(0.01)
            logger.info(line.strip().decode())

    async def _run_async(container: 'Container'):
        await asyncio.gather(
            _check_readiness(container), _stream_starting_logs(container)
        )

    try:
        client = docker.from_env()
        container: 'Container' = client.containers.get(container_id)
        asyncio.run(_run_async(container))
    finally:
        if not is_started.is_set():
            logger.error(
                f' Process terminated, the container fails to start, check the arguments or entrypoint'
            )
        is_shutdown.set()
        logger.debug(f' Process terminated')


class ContainerPea(BasePea):
    """
    :class:`ContainerPea` starts a runtime of :class:`BaseRuntime` inside a container. It leverages :class:`threading.Thread`
    or :class:`multiprocessing.Process` to manage the logs and the lifecycle of docker container object in a robust way.
    """

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)

        # start the docker
        if (
            self.args.docker_kwargs
            and 'extra_hosts' in self.args.docker_kwargs
            and __docker_host__ in self.args.docker_kwargs['extra_hosts']
        ):
            self.args.docker_kwargs.pop('extra_hosts')
        self._net_mode = None
        self.worker = None
        self.daemon = self.args.daemon  #: required here to set process/thread daemon

    def _set_network_for_dind_linux(self, client):
        import sys
        from platform import uname

        # Related to potential docker-in-docker communication. If `Runtime` lives already inside a container.
        # it will need to communicate using the `bridge` network.

        # In WSL, we need to set ports explicitly
        if sys.platform in ('linux', 'linux2') and 'microsoft' not in uname().release:
            self._net_mode = 'host'
            try:
                bridge_network = client.networks.get('bridge')
                if bridge_network:
                    self.runtime_ctrl_address = f'{bridge_network.attrs["IPAM"]["Config"][0]["Gateway"]}:{self.args.port_in}'
            except Exception as ex:
                self.logger.warning(
                    f'Unable to set control address from "bridge" network: {ex!r}'
                    f' Control address set to {self.runtime_ctrl_address}'
                )

    def _docker_run(self):
        # important to notice, that client is not assigned as instance member to avoid potential
        # heavy copy into new process memory space
        import docker
        import warnings
        from ...excepts import BadImageNameError, DockerVersionError

        client = docker.from_env()
        self._set_network_for_dind_linux(client)

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
        # basically all args in Pea-docker arg group should be ignored.
        # this prevent setting containerPea twice
        from ...parsers import set_pea_parser
        from ...helper import ArgNamespace, slugify, random_name
        from pathlib import Path

        self.args.runs_in_docker = True
        self.args.native = True

        non_defaults = ArgNamespace.get_non_defaults_args(
            self.args,
            set_pea_parser(),
            taboo={
                'uses',
                'entrypoint',
                'volumes',
                'pull_latest',
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
            device_requests = get_gpu_device_requests(self.args.gpus)
            del self.args.gpus

        _args = ArgNamespace.kwargs2list(non_defaults)
        ports = (
            {f'{self.args.port_in}/tcp': self.args.port_in}
            if not self._net_mode
            else None
        )

        docker_kwargs = self.args.docker_kwargs or {}
        self._container = client.containers.run(
            uses_img,
            _args,
            detach=True,
            auto_remove=True,
            ports=ports,
            name=slugify(f'{self.name}/{random_name()}'),
            volumes=_volumes,
            network_mode=self._net_mode,
            entrypoint=self.args.entrypoint,
            extra_hosts={__docker_host__: 'host-gateway'},
            device_requests=device_requests,
            environment=self._envs,
            **docker_kwargs,
        )
        client.close()

    def _get_control_address(self):
        """
        Get the control address for a runtime with a given host and port

        :return: The corresponding control address
        """
        import docker

        client = docker.from_env()
        network = get_docker_network(client)

        if (
            self.args.docker_kwargs
            and 'extra_hosts' in self.args.docker_kwargs
            and __docker_host__ in self.args.docker_kwargs['extra_hosts']
        ):
            ctrl_host = __docker_host__
        elif network:
            # If the caller is already in a docker network, replace ctrl-host with network gateway
            try:
                ctrl_host = client.networks.get(network).attrs['IPAM']['Config'][0][
                    'Gateway'
                ]
            except Exception:
                ctrl_host = __docker_host__
        else:
            ctrl_host = self.args.host

        client.close()
        return f'{ctrl_host}:{self.args.port_in}'

    def start(self):
        """Start the ContainerPea.
        This method calls :meth:`start` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.
        .. #noqa: DAR201
        """
        self._docker_run()

        self.worker = _get_worker(
            args=self.args,
            target=run,
            kwargs={
                'args': self.args,
                'name': self.name,
                'container_id': self._container.id,
                'runtime_ctrl_address': self.runtime_ctrl_address,
                'is_started': self.is_started,
                'is_shutdown': self.is_shutdown,
                'is_ready': self.is_ready,
            },
        )
        self.worker.start()
        if not self.args.noblock_on_start:
            self.wait_start_success()
        return self

    def _terminate(self):
        """Terminate the Pea.
        This method calls :meth:`terminate` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.
        """
        # terminate the docker
        self._container.kill(signal='SIGTERM')
        self.is_shutdown.wait(self.args.timeout_ctrl)
        if hasattr(self.worker, 'terminate'):
            self.logger.debug(f'terminating the runtime process')
            self.worker.terminate()
            self.logger.debug(f' runtime process properly terminated')
        else:
            self.logger.debug(f'canceling the runtime thread')
            self.cancel_event.set()
            self.logger.debug(f'runtime thread properly canceled')

    def join(self, *args, **kwargs):
        """Joins the Pea.
        This method calls :meth:`join` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.

        :param args: extra positional arguments to pass to join
        :param kwargs: extra keyword arguments to pass to join
        """
        import docker

        client = docker.from_env()

        try:
            containers = client.containers.list()
            while self._container.id in containers:
                time.sleep(0.1)
                containers = client.containers.list()
        except docker.errors.NotFound:
            pass
        self.logger.debug(f' Joining the process')
        self.worker.join(*args, **kwargs)
        self.logger.debug(f' Successfully joined the process')
