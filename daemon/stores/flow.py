import uuid
from typing import Optional, BinaryIO

from jina.flow import Flow
from jina.helper import colored, random_uuid
from .base import BaseStore
from .helper import jina_workspace
from ..models import UpdateOperationEnum


class FlowStore(BaseStore):
    """A Store of Flows for jinad"""

    def add(self, config: BinaryIO, workspace_id: Optional[uuid.UUID] = None, **kwargs):
        """Add a new Flow

        :param config: the binary data from the yaml
        :param workspace_id: the id of the workspace
        :param kwargs: other kwargs, not used
        :return: flow id"""
        try:
            if not workspace_id:
                workspace_id = random_uuid()

            flow_identity = random_uuid()
            with jina_workspace(workspace_id) as _workdir:
                y_spec = config.read().decode()
                f = Flow.load_config(y_spec)
                f.identity = str(flow_identity)
                f.workspace_id = str(workspace_id)
                f.start()

        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self[flow_identity] = {
                'object': f,
                'arguments': vars(f.args),
                'yaml_source': y_spec,
                'workdir': _workdir,
                'workspace_id': workspace_id,
            }
            self._logger.success(
                f'{colored(str(flow_identity), "cyan")} is added to workspace {colored(str(workspace_id), "cyan")}'
            )
            return flow_identity

    def update(
        self,
        id: 'uuid.UUID',
        kind: UpdateOperationEnum,
        dump_path: str,
        pod_name: str,
        shards: int = None,
    ):
        """Run an update operation on the Flow

        :param id: the id of the Flow
        :param kind: the kind of update operation
        :param dump_path: the dump path
        :param pod_name: the pod to target
        :param shards: the nr of shards to dump for (only used for the `dump` op)"""
        flow_dict = self._items[id]
        flow_obj = flow_dict.get('object')
        ws = flow_dict.get('workspace_id')
        with jina_workspace(ws) as _workdir:
            if kind == UpdateOperationEnum.rolling_update:
                flow_obj.rolling_update(pod_name=pod_name, dump_path=dump_path)
            elif kind == UpdateOperationEnum.dump:
                raise NotImplementedError(
                    f' sending post request does not work because asyncio loop is occupied'
                )
