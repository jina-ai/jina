import os
import re
import socket
import platform
from typing import Dict, List, Tuple, TYPE_CHECKING, Optional

import docker

from jina import __docker_host__
from jina.helper import colored
from jina.logging.logger import JinaLogger
from jina.peapods.runtimes.container.helper import get_gpu_device_requests
from . import (
    jinad_args,
    __root_workspace__,
    __partial_workspace__,
)
from .excepts import (
    DockerNotFoundException,
    DockerImageException,
    DockerNetworkException,
    DockerContainerException,
)
from .helper import id_cleaner, classproperty, is_error_message
from .models import DaemonID
from .models.enums import IDLiterals

if TYPE_CHECKING:
    from .files import DaemonFile
    from docker.models.networks import Network
    from docker.models.containers import Container
    from docker.client import APIClient, DockerClient


PORT_REGEX = r'[0-9]+(?:\.[0-9]+){3}:[0-9]+'


class Dockerizer:
    """Helper class to interact with docker client & dockerd"""

    logger = JinaLogger('Dockerizer', **vars(jinad_args))
    try:
        client: 'DockerClient' = docker.from_env()
        raw_client: 'APIClient' = docker.APIClient(
            base_url='unix://var/run/docker.sock'
        )
    except docker.errors.DockerException:
        logger.critical(
            f'docker client cannot connect to dockerd. '
            f'please start jinad with `-v /var/run/docker.sock:/var/run/docker.sock`'
        )
        raise DockerNotFoundException()

    @classmethod
    def _daemonize(cls, ids: List, attrs: str):
        for id in ids:
            try:
                field = getattr(id, attrs)
                if isinstance(field, List):
                    for f in field:
                        f = f.replace(':', '-')
                        yield DaemonID(f)
                else:
                    yield DaemonID(field)
            except TypeError:
                continue

    @classproperty
    def networks(cls) -> List[DaemonID]:
        """
        Returns all local docker networks with name in a pattern of `DaemonID`
        :return: list of networks created by jinad
        """
        return list(cls._daemonize(cls.client.networks.list(), 'name'))

    @classproperty
    def images(cls) -> List[DaemonID]:
        """
        Returns all local docker images with name in a pattern of `DaemonID`
        :return: list of images created by jinad
        """
        return list(cls._daemonize(cls.client.images.list(), 'tags'))

    @classproperty
    def containers(cls) -> List[DaemonID]:
        """
        Returns all local docker containers with name in a pattern of `DaemonID`
        :return: list of containers created by jinad
        """
        return list(cls._daemonize(cls.client.containers.list(), 'name'))

    @classmethod
    def network(cls, workspace_id: DaemonID) -> str:
        """
        Create a docker bridge network with name `workspace_id` using a predefined ipam config.
        All containers under `workspace_id` would use this network.
        :param workspace_id: workspace id
        :raises DockerNetworkException: if there are issues during network creation
        :return: id of the network
        """
        if workspace_id in cls.networks:
            network = cls.client.networks.get(network_id=workspace_id)
        else:
            from .stores import workspace_store

            new_subnet_start = (
                workspace_store.status.ip_range_start
                + workspace_store.status.ip_range_current_offset
            )

            ipam_config = docker.types.IPAMConfig(
                pool_configs=[
                    docker.types.IPAMPool(
                        subnet=f'{new_subnet_start}/{workspace_store.status.subnet_size}',
                        gateway=f'{new_subnet_start + 1}',
                    )
                ]
            )
            workspace_store.status.ip_range_current_offset += 2 ** (
                32 - workspace_store.status.subnet_size
            )
            try:
                network: 'Network' = cls.client.networks.create(
                    name=workspace_id, driver='bridge', ipam=ipam_config
                )
            except docker.errors.APIError as e:
                import traceback

                traceback.print_exc()
                cls.logger.critical(f'{e!r} during docker network creation')
                raise DockerNetworkException()
        return network.id

    @classmethod
    def build(
        cls, workspace_id: 'DaemonID', daemon_file: 'DaemonFile', logger: 'JinaLogger'
    ) -> str:
        """
        Build docker image using daemon file & tag it with `workspace_id`
        :param workspace_id: workspace id
        :param daemon_file: daemon file describing content inside the workdir
        :param logger: logger to be used
        :raises DockerImageException: if there are issues during image building
        :return: id of the image
        """
        logger.info(f'about to build image using {daemon_file}')

        def _log_stream(chunk, key):
            # logging taken from hubio.build
            _stream = chunk[key].splitlines()[0]
            if _stream:
                if is_error_message(_stream):
                    logger.critical(_stream)
                elif 'warning' in _stream.lower():
                    logger.warning(_stream)
                else:
                    logger.info(_stream)

        for build_log in cls.raw_client.build(
            path=daemon_file.dockercontext,
            dockerfile=daemon_file.dockerfile,
            buildargs=daemon_file.dockerargs,
            tag=workspace_id.tag,
            rm=True,
            pull=False,
            decode=True,
        ):
            if 'stream' in build_log:
                _log_stream(build_log, 'stream')
            elif 'message' in build_log:
                _log_stream(build_log, 'message')
            # elif 'status' in build_log:
            #     _log_stream(build_log, 'status')

        try:
            image = cls.client.images.get(name=workspace_id.tag)
        except docker.errors.ImageNotFound as e:
            logger.critical(f'Couldn\'t find image with name: {workspace_id.tag} {e!r}')
            raise DockerImageException(e)
        return id_cleaner(image.id)

    @classmethod
    def run_custom(
        cls, workspace_id: DaemonID, daemon_file: 'DaemonFile'
    ) -> Tuple['Container', str, Dict]:
        """Run a custom container during workspace creation.
        .. note::
            This invalidates the default entrypint (mini-jinad) & uses the entrypoint provided
            mentioned in the .jinad file (`run` section)
        :param workspace_id: workspace id
        :param daemon_file: daemon file describing content inside the workdir
        :return: tuple of container object, network id & ports
        """
        return cls.run(
            workspace_id=workspace_id,
            container_id=workspace_id,
            ports={f'{port}/tcp': port for port in daemon_file.ports},
            entrypoint=daemon_file.run,
        )

    @classmethod
    def run(
        cls,
        workspace_id: DaemonID,
        container_id: DaemonID,
        entrypoint: str,
        ports: Dict,
        envs: Optional[Dict] = {},
        device_requests: Optional[List] = None,
    ) -> Tuple['Container', str, Dict]:
        """
        Runs a container using an existing image (tagged with `workspace_id`).
        Maps `ports` to local dockerhost & tags the container with name `container_id`
        .. note::
            This uses the default entrypoint (mini-jinad) & appends `command` for execution.
        :param workspace_id: workspace id
        :param container_id: name of the container
        :param entrypoint: entrypoint for the container
        :param ports: ports to be mapped with local
        :param envs: dict of env vars to be set in the container
        :param device_requests: docker device requests
        :raises DockerImageException: if image is not found locally
        :raises DockerContainerException: if container creation fails
        :return: tuple of container object, network id & ports
        """

        def _validate_port_conflict(error: str) -> str:
            msg = ""
            if 'port is already allocated' in error:
                match = re.findall(PORT_REGEX, error)
                if match and len(match) > 0:
                    msg = f'port conflict: {match[0]}'
            return msg

        def _validate_device_request(error: str) -> bool:
            return True if 'could not select device driver' in error else False

        from .stores import workspace_store

        metadata = workspace_store[workspace_id].metadata
        if not metadata:
            raise DockerImageException(
                'Docker image not built properly, cannot proceed for run'
            )
        image = cls.client.images.get(name=metadata.image_id)
        network = metadata.network
        cls.logger.info(
            f'creating a container using image {colored(metadata.image_id, "cyan")} in network '
            f'{colored(network, "cyan")} and ports {colored(ports, "cyan")}'
        )
        try:
            run_kwargs = dict(
                image=image,
                name=container_id,
                volumes=cls.volume(workspace_id),
                environment=cls.environment(envs),
                network=network,
                ports=ports,
                detach=True,
                entrypoint=entrypoint,
                device_requests=device_requests or [],
                working_dir=__partial_workspace__,
                extra_hosts={__docker_host__: 'host-gateway'},
            )
            container: 'Container' = cls.client.containers.run(**run_kwargs)
        except docker.errors.NotFound as e:
            cls.logger.critical(
                f'Image {image} or Network {network} not found locally {e!r}'
            )

            raise DockerImageException(
                'Docker image not built properly, cannot proceed for run'
            )
        except docker.errors.APIError as e:
            msg = f'API Error while starting the docker container {e}'
            if _validate_device_request(str(e)):
                # It might not be possible for local to know remote machine's gpu status.
                # For few cases (Flow creation), we always set `gpus='all'`, which might fail
                # if dockerd cannot find the device. In that case, run again without device requests
                cls.logger.debug(
                    f'couldn\'t start the container with following device request. '
                    f'restarting after resetting device: {run_kwargs["device_requests"]}'
                )
                try:
                    # This leaves the old container in a "created" state and conflicts the name.
                    cls.rm_container(container_id)
                except:
                    pass
                run_kwargs.pop('device_requests')
                container: 'Container' = cls.client.containers.run(**run_kwargs)
            else:
                msg += ' ' + _validate_port_conflict(str(e))
                raise DockerContainerException(msg)
        except docker.errors.APIError as e:
            msg = f'API Error while starting the docker container{e}'
            msg += _validate_port_conflict(str(e))
            raise DockerContainerException(msg)
        # TODO: network & ports return can be avoided?
        return container, network, ports

    @classmethod
    def logs(cls, id: str) -> str:
        """Get all logs of a container

        :param id: container id
        :return: logs as str
        """
        try:
            container: 'Container' = cls.client.containers.get(container_id=id)
            return container.logs(stdout=True, stderr=True).decode()
        except docker.errors.NotFound:
            cls.logger.error(f'no containers with id {id} found')
            return ""

    @classmethod
    def _get_volume_host_dir(cls):
        try:
            volumes = cls.client.containers.get(socket.gethostname()).attrs[
                'HostConfig'
            ]['Binds']
            for volume in volumes:
                if volume.split(':')[1] == __root_workspace__:
                    return volume.split(':')[0]
        except:
            # above logic only works inside docker, if it does not work we dont need it
            pass
        return __root_workspace__

    @classproperty
    def dockersock(cls) -> str:
        """docker socket path

        :return: abs path to docker socket
        """
        location = '/var/run/docker.sock'
        return location if platform.system() == 'Darwin' else '/' + location

    @classmethod
    def volume(cls, workspace_id: DaemonID) -> Dict[str, Dict]:
        """
        Local volumes to be mounted inside the container during `run`.
        .. note::
            Local workspace should always be mounted to default WORKDIR for the container (/workspace).
            docker sock on dockerhost should also be mounted to make sure DIND works
        :param workspace_id: workspace id
        :return: dict of volume mappings
        """
        return {
            f'{cls._get_volume_host_dir()}/{workspace_id}': {
                'bind': __partial_workspace__,
                'mode': 'rw',
            },
            cls.dockersock: {'bind': '/var/run/docker.sock'},
        }

    @classmethod
    def environment(cls, envs: Dict[str, str]) -> Dict[str, str]:
        """
        Environment variables to be set inside the container during `run`

        :param envs: dict of env vars to be set in the container
        :return: dict of env vars
        """
        return {
            'JINA_LOG_WORKSPACE': os.path.join(__partial_workspace__, 'logs'),
            'JINA_RANDOM_PORT_MIN': '49153',
            'JINA_LOG_LEVEL': os.getenv('JINA_LOG_LEVEL') or 'INFO',
            'JINA_HUB_ROOT': os.path.join(
                __partial_workspace__, '.jina', 'hub-packages'
            ),
            'JINA_HUB_CACHE_DIR': os.path.join(__partial_workspace__, '.cache', 'jina'),
            'HOME': __partial_workspace__,
            **envs,
        }

    @classmethod
    def remove(cls, id: DaemonID):
        """
        Determines type of jinad object & removes that from dockerd
        :param id: `DaemonID` describing local docker object
        """
        if id.jtype == IDLiterals.JNETWORK:
            cls.rm_network(id)
        elif id.jtype == IDLiterals.JWORKSPACE:
            cls.rm_image(id)
        else:
            cls.rm_container(id)

    @classmethod
    def containers_in_network(cls, id: str) -> List:
        """Get all containers currently connected to network
        :param id: network id
        :return: list of containers connected to network id
        """
        return [
            container["Name"]
            for container in cls.raw_client.inspect_network(net_id=id)[
                'Containers'
            ].values()
        ]

    @classmethod
    def rm_network(cls, id: str) -> bool:
        """
        Remove network from local if no containers are connected
        :param id: network id
        :return: True if deletion is successful else False
        """
        try:
            containers = cls.containers_in_network(id)
            if containers:
                cls.logger.info(
                    f'following containers are still connected to the network. skipping delete {containers}'
                )
                return False

            network: 'Network' = cls.client.networks.get(id)
            network.remove()
            cls.logger.success(f'network {colored(id, "cyan")} successfully removed')
            return True
        except docker.errors.NotFound as e:
            cls.logger.error(f'Couldn\'t find a network with id: `{id}`')
            return False
        except docker.errors.APIError as e:
            cls.logger.warning(
                f'dockerd threw an error while removing the network. '
                f'There might be containers still connected to the network `{id}`: \n{e}'
            )
            return False

    @classmethod
    def rm_image(cls, id: str):
        """
        Remove image from local
        :param id: image id
        :raises KeyError: if image is not found on local
        :raises DockerImageException: error during image removal
        """
        try:
            # TODO: decide when to force
            cls.client.images.remove(id, force=True)
        except docker.errors.ImageNotFound as e:
            cls.logger.error(f'Couldn\'t fetch image with name: `{id}`')
            raise KeyError(f'image `{id}` not found')
        except docker.errors.APIError as e:
            cls.logger.error(
                f'dockerd threw an error while removing the image `{id}`: {e}'
            )
            raise DockerImageException(f'dockerd error while removing image {id} {e!r}')

    @classmethod
    def rm_container(cls, id: str):
        """
        Remove container from local
        :param id: container id
        :raises KeyError: if container is not found on local
        :raises DockerContainerException: error during container removal
        """
        try:
            container: 'Container' = cls.client.containers.get(id)
            container.stop()
            container.remove()
        except docker.errors.NotFound as e:
            cls.logger.error(f'Couldn\'t fetch container with name: `{id}`')
            raise KeyError(f'container `{id}` not found')
        except docker.errors.APIError as e:
            cls.logger.error(
                f'dockerd threw an error while removing the container `{id}`: {e}'
            )
            raise DockerContainerException(
                f'dockerd error while removing network {id} {e!r}'
            )

    @classmethod
    def _validate(cls):
        # TODO
        pass
