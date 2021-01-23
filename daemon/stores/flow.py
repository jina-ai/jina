import uuid
import argparse
from typing import List, Optional, BinaryIO

from jina.flow import Flow
from jina.helper import colored, random_uuid, random_identity
from .base import BaseStore
from .helper import jina_workspace


class FlowStore(BaseStore):

    def add(self, config: BinaryIO,
            workspace_id: Optional[uuid.UUID] = None,
            **kwargs):
        try:
            if not workspace_id:
                workspace_id = random_uuid()

            with jina_workspace(workspace_id) as _workdir:
                flow_identity = random_identity()

                y_spec = config.read().decode()
                f = Flow.load_config(y_spec)
                for _, pod in f:
                    pod.args.identity = flow_identity
                    for k, v in pod.peas_args.items():
                        if v and isinstance(v, argparse.Namespace):
                            v.workspace_id = str(workspace_id)
                        if v and isinstance(v, List):
                            for i in v:
                                i.workspace_id = str(workspace_id)
                    # pod.args.workspace_id = str(workspace_id)

                f.start()

            _id = uuid.UUID(f.args.identity)
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self[_id] = {
                'object': f,
                'arguments': vars(f.args),
                'yaml_source': y_spec,
                'workdir': _workdir,
                'workspace_id': workspace_id
            }
            self._logger.success(f'{colored(str(_id), "cyan")} is added to workspace {colored(str(workspace_id), "cyan")}')
            return _id
