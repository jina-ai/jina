import argparse
import asyncio
import copy
import multiprocessing
import os
import platform
import re
import signal
import subprocess
import threading
import time
from typing import TYPE_CHECKING, Dict, Optional, Union

from jina.constants import __docker_host__, __windows__
from jina.enums import PodRoleType
from jina.excepts import BadImageNameError, DockerVersionError
from jina.helper import random_name, slugify
from jina.importer import ImportExtensions
from jina.logging.logger import JinaLogger
from jina.orchestrate.helper import generate_default_volume_and_workspace
from jina.orchestrate.pods import BasePod
from jina.orchestrate.pods.container_helper import (
    get_docker_network,
    get_gpu_device_requests,
)
from jina.parsers import set_gateway_parser
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.gateway import GatewayRuntime

if TYPE_CHECKING:  # pragma: no cover
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
    import warnings

    import docker

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

    # the image arg should be ignored otherwise it keeps using ContainerPod in the container
    # basically all args in Pod-docker arg group should be ignored.
    # this prevent setting containerPod twice
    from pathlib import Path

    from jina.helper import ArgNamespace
    from jina.parsers import set_pod_parser

    args.native = True

    parser = (
        set_gateway_parser()
        if args.pod_role == PodRoleType.GATEWAY
        else set_pod_parser()
    )

    non_defaults = ArgNamespace.get_non_defaults_args(
        args,
        parser,
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

    if img_not_found:
        raise BadImageNameError(f'image: {uses_img} can not be found local & remote.')

    _volumes = {}
    if not getattr(args, 'disable_auto_volume', None) and not getattr(
        args, 'volumes', None
    ):
        (
            generated_volumes,
            workspace_in_container,
        ) = generate_default_volume_and_workspace(workspace_id=args.workspace_id)
        args.volumes = generated_volumes
        args.workspace = (
            workspace_in_container if not args.workspace else args.workspace
        )

    if getattr(args, 'volumes', None):
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
    if getattr(args, 'gpus', None):
        device_requests = get_gpu_device_requests(args.gpus)
        del args.gpus

    _args = ArgNamespace.kwargs2list(non_defaults)

    if args.pod_role == PodRoleType.GATEWAY:
        ports = {f'{_port}/tcp': _port for _port in args.port} if not net_mode else None
    else:
        ports = {f'{args.port}/tcp': args.port} if not net_mode else None

    if platform.system() == 'Darwin':
        try:
            host_processor_architecture = subprocess.check_output(['uname', '-p'])
        except subprocess.CalledProcessError:
            # assume it's an amd processor
            host_processor_architecture = 'amd'
        image_architecture = client.images.get(uses_img).attrs.get('Architecture', '')
        if not image_architecture.startswith(
            'arm'
        ) and host_processor_architecture.startswith('arm'):
            logger.warning(
                'Host machine uses an AMD processor but the container does not support this architecture'
            )
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

    This method is the target for the Pod's `thread` or `process`

    .. note::
        :meth:`run` is running in subprocess/thread, the exception can not be propagated to the main process.
        Hence, please do not raise any exception here.

    .. note::
        Please note that env variables are process-specific. Subprocess inherits envs from
        the main process. But Subprocess's envs do NOT affect the main process. It does NOT
        mess up user local system envs.

    :param args: namespace args from the Pod
    :param name: name of the Pod to have proper logging
    :param container_name: name to set the Container to
    :param net_mode: The network mode where to run the container
    :param runtime_ctrl_address: The control address of the runtime in the container
    :param envs: Dictionary of environment variables to be set in the docker image
    :param is_started: concurrency event to communicate runtime is properly started. Used for better logging
    :param is_shutdown: concurrency event to communicate runtime is terminated
    :param is_ready: concurrency event to communicate runtime is ready to receive messages
    """
    import docker

    log_kwargs = copy.deepcopy(vars(args))
    log_kwargs['log_config'] = 'docker'
    logger = JinaLogger(name, **log_kwargs)

    cancel = threading.Event()
    fail_to_start = threading.Event()

    if not __windows__:
        try:
            for signame in {signal.SIGINT, signal.SIGTERM}:
                signal.signal(signame, lambda *args, **kwargs: cancel.set())
        except (ValueError, RuntimeError) as exc:
            logger.warning(
                f' The process starting the container for {name} will not be able to handle termination signals. '
                f' {repr(exc)}'
            )
    else:
        with ImportExtensions(
            required=True,
            logger=logger,
            help_text='''If you see a 'DLL load failed' error, please reinstall `pywin32`.
                If you're using conda, please use the command `conda install -c anaconda pywin32`''',
        ):
            import win32api

        win32api.SetConsoleCtrlHandler(lambda *args, **kwargs: cancel.set(), True)

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
        client.close()

        def _is_ready():
            if args.pod_role == PodRoleType.GATEWAY:
                return GatewayRuntime.is_ready(
                    runtime_ctrl_address, protocol=args.protocol[0]
                )
            else:
                return AsyncNewLoopRuntime.is_ready(runtime_ctrl_address)

        def _is_container_alive(container) -> bool:
            import docker.errors

            try:
                container.reload()
            except docker.errors.NotFound:
                return False
            return True

        async def _check_readiness(container):
            while (
                _is_container_alive(container)
                and not _is_ready()
                and not cancel.is_set()
            ):
                await asyncio.sleep(0.1)
            if _is_container_alive(container):
                is_started.set()
                is_ready.set()
            else:
                fail_to_start.set()

        async def _stream_starting_logs(container):
            for line in container.logs(stream=True):
                if (
                    not is_started.is_set()
                    and not fail_to_start.is_set()
                    and not cancel.is_set()
                ):
                    await asyncio.sleep(0.01)
                msg = line.decode().rstrip()  # type: str
                logger.debug(re.sub(r'\u001b\[.*?[@-~]', '', msg))

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
        logger.debug(f'process terminated')


class ContainerPod(BasePod):
    """
    :class:`ContainerPod` starts a runtime of :class:`BaseRuntime` inside a container. It leverages :class:`multiprocessing.Process` to manage the logs and the lifecycle of docker container object in a robust way.
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

            if self.args.pod_role == PodRoleType.GATEWAY:
                ctrl_address = f'{ctrl_host}:{self.args.port[0]}'
            else:
                ctrl_address = f'{ctrl_host}:{self.args.port}'

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
                    if self.args.pod_role == PodRoleType.GATEWAY:
                        runtime_ctrl_address = f'{bridge_network.attrs["IPAM"]["Config"][0]["Gateway"]}:{self.args.port[0]}'
                    else:
                        runtime_ctrl_address = f'{bridge_network.attrs["IPAM"]["Config"][0]["Gateway"]}:{self.args.port}'
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
        """Start the ContainerPod.
        .. #noqa: DAR201
        """
        self.worker = multiprocessing.Process(
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
            daemon=True,
        )
        self.worker.start()
        if not self.args.noblock_on_start:
            self.wait_start_success()
        return self

    def _terminate(self):
        """Terminate the Pod.
        This method kills the container inside the Pod
        """
        # terminate the docker
        try:
            self._container.kill(signal='SIGTERM')
        finally:
            self.is_shutdown.wait(self.args.timeout_ctrl)
            self.logger.debug(f'terminating the runtime process')
            self.worker.terminate()
            self.logger.debug(f'runtime process properly terminated')

    def join(self, *args, **kwargs):
        """Joins the Pod.

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
        self.logger.debug(f'joining the process')
        self.worker.join(*args, **kwargs)
        self.logger.debug(f'successfully joined the process')
