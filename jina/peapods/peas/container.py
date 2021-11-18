import os
import argparse
import time

import multiprocessing
import threading

from typing import TYPE_CHECKING, Union
from typing import Union, Dict, Optional, TYPE_CHECKING
import asyncio

from . import BasePea
from .helper import _get_worker
from .container_helper import get_gpu_device_requests, get_docker_network
from ...enums import RuntimeBackendType
from ... import __docker_host__
from ...logging.logger import JinaLogger
from ...helper import slugify, random_name
from ..runtimes.asyncio import AsyncNewLoopRuntime

if TYPE_CHECKING:
    from docker.models.containers import Container
    from docker.client import DockerClient


def _docker_run(
    client: 'DockerClient',
    args: 'argparse.Namespace',
    container_name: str,
    envs: Dict,
    net_mode: Optional[str],
    logger: 'JinaLogger',
):
    # important to notice, that client is not assigned as instance member to avoid potential
    # heavy copy into new process memory space
    import docker
    import warnings
    from ...excepts import BadImageNameError, DockerVersionError

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

    if args.uses.startswith('docker://'):
        uses_img = args.uses.replace('docker://', '')
        logger.debug(f'will use Docker image: {uses_img}')
    else:
        warnings.warn(
            f'you are using legacy image format {args.uses}, this may create some ambiguity. '
            f'please use the new format: "--uses docker://{args.uses}"'
        )
        uses_img = args.uses

    # the image arg should be ignored otherwise it keeps using ContainerPea in the container
    # basically all args in Pea-docker arg group should be ignored.
    # this prevent setting containerPea twice
    from ...parsers import set_pea_parser
    from ...helper import ArgNamespace
    from pathlib import Path

    args.runs_in_docker = True
    args.native = True

    non_defaults = ArgNamespace.get_non_defaults_args(
        args,
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
        logger.error(f'can not find local image: {uses_img}')
        img_not_found = True

    if args.pull_latest or img_not_found:
        logger.warning(
            f'pulling {uses_img}, this could take a while. if you encounter '
            f'timeout error due to pulling takes to long, then please set '
            f'"timeout-ready" to a larger value.'
        )
        try:
            client.images.pull(uses_img)
            img_not_found = False
        except docker.errors.NotFound:
            img_not_found = True
            logger.error(f'can not find remote image: {uses_img}')

    if img_not_found:
        raise BadImageNameError(f'image: {uses_img} can not be found local & remote.')

    _volumes = {}
    if args.volumes:
        for p in args.volumes:
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
    if args.gpus:
        device_requests = get_gpu_device_requests(args.gpus)
        del args.gpus

    _args = ArgNamespace.kwargs2list(non_defaults)
    ports = {f'{args.port_in}/tcp': args.port_in} if not net_mode else None

    docker_kwargs = args.docker_kwargs or {}
    container = client.containers.run(
        uses_img,
        _args,
        detach=True,
        auto_remove=True,
        ports=ports,
        name=container_name,
        volumes=_volumes,
        network_mode=net_mode,
        entrypoint=args.entrypoint,
        extra_hosts={__docker_host__: 'host-gateway'},
        device_requests=device_requests,
        environment=envs,
        **docker_kwargs,
    )
    return container


def run(
    args: 'argparse.Namespace',
    name: str,
    container_name: str,
    net_mode: Optional[str],
    runtime_ctrl_address: str,
    envs: Dict,
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
    :param container_name: name to set the Container to
    :param net_mode: The network mode where to run the container
    :param runtime_ctrl_address: The control address of the runtime in the container
    :param envs: Dictionary of environment variables to be set in the docker image
    :param is_started: concurrency event to communicate runtime is properly started. Used for better logging
    :param is_shutdown: concurrency event to communicate runtime is terminated
    :param is_ready: concurrency event to communicate runtime is ready to receive messages
    """
    import docker

    logger = JinaLogger(name, **vars(args))
    _fail_to_start = asyncio.Event()

    client = docker.from_env()

    try:
        container = _docker_run(
            client=client,
            args=args,
            container_name=container_name,
            envs=envs,
            net_mode=net_mode,
            logger=logger,
        )
        # client.close()

        def _is_ready():
            return AsyncNewLoopRuntime.is_ready(runtime_ctrl_address)

        def _is_container_alive(container) -> bool:
            import docker.errors

            try:
                container.reload()
            except docker.errors.NotFound:
                return False
            return True

        async def _check_readiness(container):
            while _is_container_alive(container) and not _is_ready():
                await asyncio.sleep(0.1)
            if _is_container_alive(container):
                is_started.set()
                is_ready.set()
            else:
                _fail_to_start.set()

        async def _stream_starting_logs(container):
            for line in container.logs(stream=True):
                if not is_started.is_set() and not _fail_to_start.is_set():
                    await asyncio.sleep(0.01)
                logger.info(line.strip().decode())

        async def _run_async(container):
            await asyncio.gather(
                *[_check_readiness(container), _stream_starting_logs(container)]
            )

        asyncio.run(_run_async(container))
    finally:
        client.close()
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
        if (
            self.args.docker_kwargs
            and 'extra_hosts' in self.args.docker_kwargs
            and __docker_host__ in self.args.docker_kwargs['extra_hosts']
        ):
            self.args.docker_kwargs.pop('extra_hosts')
        self._net_mode = None
        self.worker = None
        self.daemon = self.args.daemon  #: required here to set process/thread daemon
        self.container_name = slugify(f'{self.name}/{random_name()}')
        self.net_mode, self.runtime_ctrl_address = self._get_control_address()

    def _get_control_address(self):
        import docker

        client = docker.from_env()
        try:
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
                except:
                    ctrl_host = __docker_host__
            else:
                ctrl_host = self.args.host

            ctrl_address = f'{ctrl_host}:{self.args.port_in}'

            net_node, runtime_ctrl_address = self._get_network_for_dind_linux(
                client, ctrl_address
            )
        finally:
            client.close()

        return net_node, runtime_ctrl_address

    def _get_network_for_dind_linux(self, client: 'DockerClient', ctrl_address: str):
        import sys
        from platform import uname

        # Related to potential docker-in-docker communication. If `Runtime` lives already inside a container.
        # it will need to communicate using the `bridge` network.

        # In WSL, we need to set ports explicitly
        net_mode, runtime_ctrl_address = None, ctrl_address
        if sys.platform in ('linux', 'linux2') and 'microsoft' not in uname().release:
            net_mode = 'host'
            try:
                bridge_network = client.networks.get('bridge')
                if bridge_network:
                    runtime_ctrl_address = f'{bridge_network.attrs["IPAM"]["Config"][0]["Gateway"]}:{self.args.port_in}'
            except Exception as ex:
                self.logger.warning(
                    f'Unable to set control address from "bridge" network: {ex!r}'
                    f' Control address set to {runtime_ctrl_address}'
                )

        return net_mode, runtime_ctrl_address

    @property
    def _container(self):
        import docker

        client = docker.from_env()
        container = None
        try:
            container = client.containers.get(self.container_name)
        finally:
            client.close()
        return container

    def start(self):
        """Start the ContainerPea.
        This method calls :meth:`start` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.
        .. #noqa: DAR201
        """
        self.worker = _get_worker(
            args=self.args,
            target=run,
            kwargs={
                'args': self.args,
                'name': self.name,
                'container_name': self.container_name,
                'net_mode': self.net_mode,
                'runtime_ctrl_address': self.runtime_ctrl_address,
                'envs': self._envs,
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
        try:
            self._container.kill(signal='SIGTERM')
        finally:
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
            container_id = self._container.id
            containers = client.containers.list()
            while container_id in containers:
                time.sleep(0.1)
                containers = client.containers.list()
        except docker.errors.NotFound:
            pass
        self.logger.debug(f' Joining the process')
        self.worker.join(*args, **kwargs)
        self.logger.debug(f' Successfully joined the process')
