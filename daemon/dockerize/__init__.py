from typing import Dict, List, Tuple, Union, TYPE_CHECKING

import docker
from fastapi import HTTPException
from jina import __ready_msg__
from jina.logging import JinaLogger
from ..models import DaemonID
from ..models.enums import IDLiterals
from ..helper import id_cleaner, classproperty
from .. import __rootdir__, __dockerfiles__, __root_workspace__, jinad_args

__flow_ready__ = 'Flow is ready to use'


if TYPE_CHECKING:
    from ..stores.workspaces import DaemonFile
    from docker.client import APIClient, DockerClient
    from docker.models.networks import Network
    from docker.models.containers import Container


class Dockerizer:

    client: 'DockerClient' = docker.from_env()
    raw_client: 'APIClient' = docker.APIClient(base_url='unix://var/run/docker.sock')
    logger = JinaLogger('Dockerizer', **vars(jinad_args))

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
        network: 'Network' = cls.client.networks.create(
            name=workspace_id, driver='bridge'
        )
        return network.id

    @classmethod
    def build(cls, workspace_id: 'DaemonID', daemon_file: 'DaemonFile') -> str:
        for build_logs in cls.raw_client.build(
            path=daemon_file.dockercontext,
            dockerfile=daemon_file.dockerfile,
            tag=workspace_id.tag,
            rm=True,
            pull=True,
            decode=True,
        ):
            if 'stream' in build_logs:
                _stream = build_logs['stream'].splitlines()[0]
                if _stream:
                    cls.logger.info(_stream)
        image = cls.client.images.get(name=workspace_id.tag)
        return id_cleaner(image.id)

    @classmethod
    def run(
        cls,
        workspace_id: DaemonID,
        container_id: DaemonID,
        command: str,
        ports: Dict,
        additional_ports: Tuple[int, int],
    ) -> Tuple['Container', str, Dict, bool]:
        from ..stores import workspace_store

        metadata = workspace_store[workspace_id]['metadata']

        _image = cls.client.images.get(name=metadata['image_id'])
        _network = metadata['network']
        _min_port, _max_port = additional_ports
        # TODO: Handle port mappings
        # ports.update(
        #     {f'{port}/tcp': port for port in range(_min_port, _max_port + 1)}
        # )
        cls.logger.info(
            f'Creating a container using image {_image} in network {_network}'
        )
        try:
            container: 'Container' = cls.client.containers.run(
                image=_image,
                name=container_id,
                volumes=cls.volume(workspace_id),
                environment=cls.environment(workspace_id, _min_port, _max_port),
                network=_network,
                ports=ports,
                detach=True,
                command=command,
            )
        except docker.errors.NotFound as e:
            cls.logger.error(
                f'Image {_image} or Network {_network} not found locally {e}'
            )

        _msg_to_check = __flow_ready__ if container_id.type == 'flow' else __ready_msg__

        # TODO: Super ugly way of knowing if the "start" was successful
        _success = False
        for run_logs in container.logs(stream=True, follow=True):
            _log_line = run_logs.splitlines()[0].decode()
            cls.logger.info(_log_line)
            if _msg_to_check in _log_line:
                cls.logger.success(
                    f'{container_id.type.title()} object is now ready to use!'
                )
                _success = True
                break
        return container, _network, ports, _success

    @classmethod
    def volume(cls, workspace_id: DaemonID) -> Dict[str, Dict]:
        return {
            f'{__root_workspace__}/{workspace_id}': {
                'bind': '/workspace',
                'mode': 'rw',
            }
        }

    @classmethod
    def environment(
        cls, workspace_id: DaemonID, min_port: int, max_port: int
    ) -> Dict[str, str]:
        return {
            'JINA_LOG_WORKSPACE': '/workspace/logs',
            'JINA_RANDOM_PORTS': 'True',
            'JINA_RANDOM_PORT_MIN': str(min_port),
            'JINA_RANDOM_PORT_MAX': str(max_port),
        }

    def remove(cls, id: DaemonID):
        if id.jtype == IDLiterals.JNETWORK:
            cls.rm_network(id)
        elif id.jtype == IDLiterals.JWORKSPACE:
            cls.rm_image(id)
        else:
            cls.rm_container(id)

    @classmethod
    def rm_network(cls, id: DaemonID):
        try:
            network: 'Network' = cls.client.networks.get(id)
            network.remove()
        except docker.errors.NotFound as e:
            cls.logger.error(f'Couldn\'t fetch network with id: `{id}`')
            raise HTTPException(status_code=404, detail=f'Network `{id}` not found')
        except docker.errors.APIError as e:
            cls.logger.error(
                f'Dockerd threw an error while removing the network `{id}`: {e}'
            )
            raise HTTPException(
                status_code=400, detail=f'dockerd error while removing network `{id}`'
            )

    @classmethod
    def rm_image(cls, id: DaemonID):
        try:
            # TODO: decide when to force
            cls.client.images.remove(id, force=True)
        except docker.errors.ImageNotFound as e:
            cls.logger.error(f'Couldn\'t fetch image with name: `{id}`')
            raise HTTPException(status_code=404, detail=f'Image `{id}` not found')

    @classmethod
    def rm_container(cls, id: DaemonID):
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
