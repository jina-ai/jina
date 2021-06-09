from jina.helper import colored
from typing import Dict, List, Tuple, TYPE_CHECKING

import docker
from fastapi import HTTPException

from jina import __ready_msg__
from jina.logging.logger import JinaLogger
from jina.docker.checker import is_error_message

from .models import DaemonID
from .models.enums import IDLiterals
from .helper import id_cleaner, classproperty
from . import (
    __rootdir__,
    __dockerfiles__,
    __root_workspace__,
    jinad_args,
    __dockerhost__,
)
from .excepts import (
    DockerNotFoundException,
    DockerBuildException,
    DockerNetworkException,
    DockerRunException,
)

__flow_ready__ = 'Flow is ready to use'


if TYPE_CHECKING:
    from .files import DaemonFile
    from docker.models.networks import Network
    from docker.models.containers import Container
    from docker.client import APIClient, DockerClient


class Dockerizer:

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
    def daemonize(cls, ids: List, attrs: str):
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
        return list(cls.daemonize(cls.client.networks.list(), 'name'))

    @classproperty
    def images(cls) -> List[DaemonID]:
        return list(cls.daemonize(cls.client.images.list(), 'tags'))

    @classproperty
    def containers(cls) -> List[DaemonID]:
        return list(cls.daemonize(cls.client.containers.list(), 'name'))

    @classmethod
    def network(cls, workspace_id: DaemonID) -> str:
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
                        gateway=f'{new_subnet_start+1}',
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
            elif 'status' in build_log:
                _log_stream(build_log, 'status')

        try:
            image = cls.client.images.get(name=workspace_id.tag)
        except docker.errors.ImageNotFound as e:
            logger.critical(f'Couldn\'t find image with name: {workspace_id.tag} {e!r}')
            raise DockerBuildException(e)
        return id_cleaner(image.id)

    @classmethod
    def run(
        cls,
        workspace_id: DaemonID,
        container_id: DaemonID,
        command: str,
        ports: Dict,
    ) -> Tuple['Container', str, Dict]:
        from .stores import workspace_store

        metadata = workspace_store[workspace_id].metadata
        if not metadata:
            raise DockerBuildException(
                'Docker image not built properly, cannot proceed for run'
            )
        image = cls.client.images.get(name=metadata.image_id)
        network = metadata.network
        cls.logger.info(
            f'Creating a container using image {colored(metadata.image_id, "cyan")} in network '
            f'{colored(network, "cyan")} and ports {colored(ports, "cyan")}'
        )
        try:
            container: 'Container' = cls.client.containers.run(
                image=image,
                name=container_id,
                volumes=cls.volume(workspace_id),
                environment=cls.environment(),
                network=network,
                ports=ports,
                detach=True,
                command=command,
                extra_hosts={__dockerhost__: 'host-gateway'},
            )
        except docker.errors.NotFound as e:
            cls.logger.critical(
                f'Image {image} or Network {network} not found locally {e!r}'
            )
            raise DockerBuildException(
                'Docker image not built properly, cannot proceed for run'
            )
        except docker.errors.APIError as e:
            import traceback

            cls.logger.critical(traceback.format_exc())
            cls.logger.critical(f'API Error while starting the docker container \n{e}')
            raise DockerRunException()
        return container, network, ports

    @classmethod
    def volume(cls, workspace_id: DaemonID) -> Dict[str, Dict]:
        return {
            f'{__root_workspace__}/{workspace_id}': {
                'bind': '/workspace',
                'mode': 'rw',
            },
            # TODO: without adding slash, it fails on WSL (needs to checked on linux/mac)
            '//var/run/docker.sock': {'bind': '/var/run/docker.sock'},
        }

    @classmethod
    def environment(cls) -> Dict[str, str]:
        return {'JINA_LOG_WORKSPACE': '/workspace/logs', 'JINA_RANDOM_PORTS': 'True'}

    def remove(cls, id: DaemonID):
        if id.jtype == IDLiterals.JNETWORK:
            cls.rm_network(id)
        elif id.jtype == IDLiterals.JWORKSPACE:
            cls.rm_image(id)
        else:
            cls.rm_container(id)

    @classmethod
    def rm_network(cls, id: str):
        try:
            network: 'Network' = cls.client.networks.get(id)
            network.remove()
        except docker.errors.NotFound as e:
            cls.logger.error(f'Couldn\'t fetch network with id: `{id}`')
            raise HTTPException(status_code=404, detail=f'Network `{id}` not found')
        except docker.errors.APIError as e:
            cls.logger.error(
                f'dockerd threw an error while removing the network `{id}`: {e}'
            )
            raise HTTPException(
                status_code=400, detail=f'dockerd error while removing network `{id}`'
            )

    @classmethod
    def rm_image(cls, id: str):
        try:
            # TODO: decide when to force
            cls.client.images.remove(id, force=True)
        except docker.errors.ImageNotFound as e:
            cls.logger.error(f'Couldn\'t fetch image with name: `{id}`')
            raise HTTPException(status_code=404, detail=f'Image `{id}` not found')

    @classmethod
    def rm_container(cls, id: str):
        try:
            container: 'Container' = cls.client.containers.get(id)
        except docker.errors.NotFound as e:
            cls.logger.error(f'Couldn\'t fetch container with name: `{id}`')
            raise HTTPException(status_code=404, detail=f'Container `{id}` not found')
        else:
            container.stop()
            container.remove()

    @classmethod
    def validate(cls):
        pass
