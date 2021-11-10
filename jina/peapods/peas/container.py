import os
import argparse
import time

from typing import Tuple, Any, Union, Optional, Dict, TYPE_CHECKING

from . import BasePea
from .container_helper import get_gpu_device_requests, get_docker_network
from ...enums import RuntimeBackendType
from ..zmq import Zmqlet
from ... import __ready_msg__, __docker_host__
from ...excepts import RuntimeFailToStart
from ...logging.logger import JinaLogger
from ...helper import typename

if TYPE_CHECKING:
    import multiprocessing
    import threading


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
    from ..zmq import send_ctrl_message

    logger = JinaLogger(name, **vars(args))

    def _is_ready():
        status = send_ctrl_message(
            runtime_ctrl_address, 'STATUS', timeout=args.timeout_ctrl
        )
        return status and status.is_ready

    def _is_container_alive(container) -> bool:
        import docker.errors

        try:
            container.reload()
        except docker.errors.NotFound:
            return False
        return True

    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        while _is_container_alive(container) and not _is_ready():
            time.sleep(1)
        # two cases to reach here: 1. is_ready, 2. container is dead
        if not _is_container_alive(container):
            logger.error(f' Process terminated')(
                'the container fails to start, check the arguments or entrypoint'
            )
        else:
            is_started.set()
            is_ready.set()
            for line in container.logs(stream=True):
                logger.info(line.strip().decode())
    finally:
        is_shutdown.set()
        logger.debug(f' Process terminated')


class ContainerPea(BasePea):
    """
    :class:`ContainerPea` starts a runtime of :class:`BaseRuntime` inside a container. It leverages :class:`threading.Thread`
    or :class:`multiprocessing.Process` to manage the logs and the lifecycle of docker container object in a robust way.
    """

    def __init__(self, args: 'argparse.Namespace'):
        super().__init__(args)

        self.runtime_ctrl_address = self.get_control_address(
            self.args.host,
            self.args.port_ctrl,
            docker_kwargs=self.args.docker_kwargs,
        )

        # start the docker
        if (
            self.args.docker_kwargs
            and 'extra_hosts' in self.args.docker_kwargs
            and __docker_host__ in self.args.docker_kwargs['extra_hosts']
        ):
            self.args.docker_kwargs.pop('extra_hosts')
        self._net_mode = None
        self._set_network_for_dind_linux()
        self._docker_run()

        self.worker = {
            RuntimeBackendType.THREAD: threading.Thread,
            RuntimeBackendType.PROCESS: multiprocessing.Process,
        }.get(getattr(args, 'runtime_backend', RuntimeBackendType.THREAD))(
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
        self.daemon = self.args.daemon  #: required here to set process/thread daemon

    def _set_network_for_dind_linux(self):
        import sys
        import docker
        from platform import uname

        # recompute the control_addr, do not assign client, since this would be an expensive object to
        # copy in the new process generated
        client = docker.from_env()

        # Related to potential docker-in-docker communication. If `Runtime` lives already inside a container.
        # it will need to communicate using the `bridge` network.

        # In WSL, we need to set ports explicitly
        if sys.platform in ('linux', 'linux2') and 'microsoft' not in uname().release:
            self._net_mode = 'host'
            try:
                bridge_network = client.networks.get('bridge')
                if bridge_network:
                    self.runtime_ctrl_address, _ = Zmqlet.get_ctrl_address(
                        bridge_network.attrs['IPAM']['Config'][0]['Gateway'],
                        self.args.port_ctrl,
                        self.args.ctrl_with_ipc,
                    )
            except Exception as ex:
                self.logger.warning(
                    f'Unable to set control address from "bridge" network: {ex!r}'
                    f' Control address set to {self.runtime_ctrl_address}'
                )
        client.close()

    def _docker_run(self):
        # important to notice, that client is not assigned as instance member to avoid potential
        # heavy copy into new process memory space
        import docker
        import warnings
        from ...excepts import BadImageNameError, DockerVersionError

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
            device_requests = get_gpu_device_requests(self.args.gpus)
            del self.args.gpus

        _expose_port = [self.args.port_ctrl]
        if self.args.socket_in.is_bind:
            _expose_port.append(self.args.port_in)
        if self.args.socket_out.is_bind:
            _expose_port.append(self.args.port_out)

        _args = ArgNamespace.kwargs2list(non_defaults)
        ports = {f'{v}/tcp': v for v in _expose_port} if not self._net_mode else None

        # WORKAROUND: we cant automatically find these true/false flags, this needs to be fixed
        if 'dynamic_routing' in non_defaults and not non_defaults['dynamic_routing']:
            _args.append('--no-dynamic-routing')

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
            **docker_kwargs,
        )

        client.close()

    @staticmethod
    def get_control_address(
        host: str,
        port: str,
        docker_kwargs: Optional[Dict],
        **kwargs,
    ):
        """
        Get the control address for a runtime with a given host and port

        :param host: the host where the runtime works
        :param port: the control port where the runtime listens
        :param docker_kwargs: the extra docker kwargs from which maybe extract extra hosts
        :param kwargs: extra keyword arguments
        :return: The corresponding control address
        """
        import docker

        client = docker.from_env()
        network = get_docker_network(client)

        if (
            docker_kwargs
            and 'extra_hosts' in docker_kwargs
            and __docker_host__ in docker_kwargs['extra_hosts']
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
            ctrl_host = host

        return Zmqlet.get_ctrl_address(ctrl_host, port, False)[0]

    def start(self):
        """Start the ContainerPea.
        This method calls :meth:`start` in :class:`threading.Thread` or :class:`multiprocesssing.Process`. The process will check the readiness
        of the container and stream its logs
        .. #noqa: DAR201
        """
        self.worker.start()
        if not self.args.noblock_on_start:
            self.wait_start_success()
        return self

    def _terminate(self):
        """Terminate the Pea.
        This method calls :meth:`terminate` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.
        """
        if hasattr(self.worker, 'terminate'):
            self.logger.debug(f' terminating the runtime process')
            self.worker.terminate()
            self.logger.debug(f' runtime process properly terminated')
        # also terminate the docker

    def _cancel_runtime(self, skip_deactivate: bool = False):
        """
        Send terminate control message.

        :param skip_deactivate: Mark that the DEACTIVATE signal may be missed if set to True
        """
        self.runtime_cls.cancel(
            cancel_event=self.cancel_event,
            logger=self.logger,
            socket_in_type=self.args.socket_in,
            control_address=self.runtime_ctrl_address,
            timeout_ctrl=self._timeout_ctrl,
            skip_deactivate=skip_deactivate,
        )

    def _get_runtime_cls(self) -> Tuple[Any, bool]:
        from ..runtimes import get_runtime

        return get_runtime(self.args.runtime_cls)

    def _wait_for_ready_or_shutdown(self, timeout: Optional[float]):
        """
        Waits for the process to be ready or to know it has failed.

        :param timeout: The time to wait before readiness or failure is determined
            .. # noqa: DAR201
        """
        return self.runtime_cls.wait_for_ready_or_shutdown(
            timeout=timeout,
            ready_or_shutdown_event=self.ready_or_shutdown.event,
            ctrl_address=self.runtime_ctrl_address,
            timeout_ctrl=self._timeout_ctrl,
            shutdown_event=self.is_shutdown,
        )

    def _check_failed_to_start(self):
        """
        Raises a corresponding exception if failed to start
        """
        if self.is_shutdown.is_set() and not self.is_started.is_set():
            # return too early and the shutdown is set, means something fails!!
            raise RuntimeFailToStart

    def _fail_start_timeout(self, timeout):
        """
        Closes the Pea and raises a TimeoutError with the corresponding warning messages

        :param timeout: The time to wait before readiness or failure is determined
            .. # noqa: DAR201
        """
        _timeout = timeout or -1
        self.logger.warning(
            f'{self.runtime_cls!r} timeout after waiting for {self.args.timeout_ready}ms, '
            f'if your executor takes time to load, you may increase --timeout-ready'
        )
        self.close()
        raise TimeoutError(
            f'{typename(self)}:{self.name} can not be initialized after {_timeout * 1e3}ms'
        )

    def wait_start_success(self):
        """Block until all peas starts successfully.

        If not success, it will raise an error hoping the outer function to catch it
        """
        _timeout = self.args.timeout_ready
        if _timeout <= 0:
            _timeout = None
        else:
            _timeout /= 1e3

        if self._wait_for_ready_or_shutdown(_timeout):
            self._check_failed_to_start()
            self.logger.debug(__ready_msg__)
        else:
            self._fail_start_timeout(_timeout)

    def join(self, *args, **kwargs):
        """Joins the Pea.
        This method calls :meth:`join` in :class:`threading.Thread` or :class:`multiprocesssing.Process`.

        :param args: extra positional arguments to pass to join
        :param kwargs: extra keyword arguments to pass to join
        """
        self.logger.debug(f' Joining the process')
        self.worker.join(*args, **kwargs)
        self.logger.debug(f' Successfully joined the process')
