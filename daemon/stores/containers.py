from typing import Dict

from jina.helper import colored, ArgNamespace, random_port
from .base import BaseStore
from ..dockerize import Dockerizer
from ..excepts import Runtime400Exception
from ..helper import id_cleaner, random_port_range
from ..models import DaemonID
from ..models.containers import (
    ContainerArguments,
    ContainerItem,
    ContainerMetadata,
    ContainerStoreStatus,
)


class ContainerStore(BaseStore):
    """A Store of Containers spawned by daemon"""

    _kind = 'container'
    _status_model = ContainerStoreStatus

    @BaseStore.dump
    def add(
        self, id: DaemonID, workspace_id: DaemonID, params: str, ports: Dict, **kwargs
    ):
        try:
            from . import workspace_store

            if workspace_id not in workspace_store:
                raise KeyError(f'{workspace_id} not found in workspace store')

            rest_api_port = random_port()
            command = f'jinad-partial --mode {self._kind} --rest-api-port {rest_api_port} {" ".join(ArgNamespace.kwargs2list(params.dict(exclude={"log_config"})))}'

            ports[f'{rest_api_port}/tcp'] = rest_api_port

            _container, _network, _ports, _success, ip_address = Dockerizer.run(
                workspace_id=workspace_id,
                container_id=id,
                command=command,
                ports=ports,
                additional_ports=random_port_range(count=30),
            )
            if not _success:
                raise Runtime400Exception(f'{id.type} creation failed')

        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:

            self[id] = ContainerItem(
                metadata=ContainerMetadata(
                    container_id=id_cleaner(_container.id),
                    container_name=_container.name,
                    image_id=id_cleaner(_container.image.id),
                    network=_network,
                    ports=_ports,
                    rest_api_uri=f'{ip_address}:{rest_api_port}',
                ),
                arguments=ContainerArguments(command=command),
                workspace_id=workspace_id,
            )
            self._logger.success(
                f'{colored(str(id), "cyan")} is added to workspace '
                f'{colored(str(workspace_id), "cyan")}'
            )
            return id

    @BaseStore.dump
    def delete(self, id: DaemonID, **kwargs):
        if id in self:
            Dockerizer.rm_container(id=self[id].metadata.container_id)
            del self[id]
            self._logger.success(
                f'{colored(str(id), "cyan")} is released from the store.'
            )
        else:
            raise KeyError(f'{colored(id, "cyan")} not found in store.')


class PeaStore(ContainerStore):
    _kind = 'pea'


class PodStore(ContainerStore):
    _kind = 'pod'


class FlowStore(ContainerStore):
    _kind = 'flow'
