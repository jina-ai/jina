import docker
from typing import List, Tuple, Union, TYPE_CHECKING

from jina import __ready_msg__
from jina.logging import JinaLogger
from ..models import DaemonID
from .helper import id_cleaner
from .. import __rootdir__, __dockerfiles__, __root_workspace__, jinad_args

__flow_ready__ = 'Flow is ready to use'


if TYPE_CHECKING:
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

    @property
    @classmethod
    def networks(cls) -> List[DaemonID]:
        return list(cls.daemonize(cls.client.networks.list(), 'name'))

    @property
    @classmethod
    def images(cls) -> List[DaemonID]:
        return list(cls.daemonize(cls.client.images.list(), 'tags'))

    @property
    @classmethod
    def containers(cls) -> List[DaemonID]:
        return list(cls.daemonize(cls.client.containers.list(), 'name'))

    @classmethod
    def network(cls, workspace_id: DaemonID):
        network: 'Network' = cls.client.networks.create(name=workspace_id, driver='bridge')
        return network.name

    @classmethod
    def build(cls, workspace_id: DaemonID) -> str:
        for build_logs in cls.raw_client.build(path=__rootdir__,
                                                dockerfile=f'{__dockerfiles__}/devel.Dockerfile',
                                                tag=workspace_id.tag,
                                                rm=True,
                                                pull=True,
                                                decode=True):
            if 'stream' in build_logs:
                if build_logs['stream'].splitlines()[0]:
                    cls.logger.info(build_logs['stream'].splitlines()[0])
        image = cls.client.images.get(name=workspace_id.tag)
        return id_cleaner(image.id)

    @classmethod
    def run(cls,
            workspace_id: DaemonID,
            container_id: DaemonID,
            command: str) -> Tuple['Container', str, bool]:
        from ..stores import workspace_store

        metadata = workspace_store[workspace_id]['metadata']
        _image = cls.client.images.get(name=metadata['image_id'])
        _network = metadata['network']
        cls.logger.info(f'Creating a container using image {_image} in network {_network}')

        container: 'Container' = cls.client.containers.run(
            image=_image,
            name=container_id,
            volumes={f'{__root_workspace__}/{workspace_id}': {'bind': '/workspace', 'mode': 'rw'}},
            network=_network,
            detach=True,
            command=command
        )

        _msg_to_check = __flow_ready__ if container_id.type == 'flow' else __ready_msg__

        # TODO: Check status of new container properly
        _success = False
        for run_logs in container.logs(stream=True, follow=True):
            _log_line = run_logs.splitlines()[0].decode()
            cls.logger.info(_log_line)
            if _msg_to_check in _log_line:
                cls.logger.success(f'{container_id.type.title()} object is now ready to use!')
                _success = True
                break
        return container, _network, _success

    @classmethod
    def rm_network(cls, id: DaemonID):
        try:
            network: 'Network' = cls.client.networks.get(id)
        except docker.errors.NotFound as e:
            cls.logger.error(f'Couldn\'t fetch network with name: {id}')
            raise
        else:
            network.remove()

    @classmethod
    def rm_image(cls, id: DaemonID):
        try:
            cls.client.images.remove(id)
        except docker.errors.ImageNotFound as e:
            cls.logger.error(f'Couldn\'t fetch image with name: {id}')
            raise

    @classmethod
    def rm_container(cls, id: DaemonID):
        try:
            container: 'Container' = cls.client.containers.get(id)
        except docker.errors.NotFound as e:
            cls.logger.error(f'Couldn\'t fetch container with name: {id}')
            raise
        else:
            container.stop()
            container.remove()

    @classmethod
    def validate(cls):
        pass
