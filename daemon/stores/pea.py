import uuid
from argparse import Namespace

from jina.helper import random_uuid, colored
from jina.peapods import Pea
from .workunit import WorkunitStore
from .helper import jina_workspace


class PeaStore(WorkunitStore):
    peapod_cls = Pea

    def add(self, args: Namespace, **kwargs):
        try:
            workspace_id = args.workspace_id
            if not workspace_id:
                workspace_id = random_uuid()
            else:
                workspace_id = uuid.UUID(workspace_id)

            with jina_workspace(workspace_id) as _workdir:
                p = self.peapod_cls(args).start()

            _id = uuid.UUID(args.identity)
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self[_id] = {
                'object': p,
                'arguments': vars(args),
                'workdir': _workdir,
                'workspace_id': workspace_id,
            }
            self._workspace_store[workspace_id] = {
                'arguments': [],
                'workdir': _workdir,
                'workspace_id': workspace_id,
            }
            self._logger.success(
                f'{colored(str(_id), "cyan")} is added to workspace {colored(str(workspace_id), "cyan")}'
            )
            return _id
