import os
import shutil
from pathlib import Path
from typing import List
from fastapi import UploadFile

from jina.helper import colored
from .base import BaseStore, Dockerizer
from ..models import DaemonID
from .. import __rootdir__, __dockerfiles__
from .helper import get_workspace_path


class WorkspaceStore(BaseStore):

    _kind = 'workspace'

    def _handle_files(self,
                      workspace_id: DaemonID,
                      workdir: str,
                      files: List[UploadFile]):
        Path(workdir).mkdir(parents=True, exist_ok=True)
        for f in files:
            dest = os.path.join(workdir, f.filename)
            if os.path.isfile(dest):
                self._logger.warning(
                    f'file {f.filename} already exists in workspace {workspace_id}, will be replaced'
                )
            with open(dest, 'wb+') as fp:
                content = f.file.read()
                fp.write(content)
            self._logger.info(f'saved uploads to {dest}')

    def add(self, files: List[UploadFile], **kwargs):
        try:
            workspace_id = DaemonID('jworkspace')
            workdir = get_workspace_path(workspace_id)
            self._handle_files(workspace_id=workspace_id, workdir=workdir, files=files)
            network = Dockerizer.network(workspace_id=workspace_id)
            image_id = Dockerizer.build(workspace_id=workspace_id)
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self[workspace_id] = {
                'metadata': {
                    'image_id': image_id,
                    'image_name': workspace_id.tag,
                    'network': network,
                    'workdir': workdir
                },
                'arguments': {
                    'files': [f.filename for f in files],
                    'jinad': ',jinad',
                    'requirements': []
                }
            }
            self._logger.info(self[workspace_id])
            self.dump()
            return workspace_id

    def update(self, workspace_id: DaemonID, files: List[UploadFile], **kwargs) -> DaemonID:
        try:
            self._handle_files(workspace_id=workspace_id, files=files)
            _image_id = Dockerizer.build(workspace_id=workspace_id)
        except Exception as e:
            self._logger.error(f'{e!r}')
            raise
        else:
            self[workspace_id]['arguments'].extend([f.filename for f in files])
            self[workspace_id]['metadata']['image-id'] = _image_id
            self.dump()
            return workspace_id

    def delete(self, id: DaemonID, **kwargs):
        if id in self._items:
            Dockerizer.rm_image(id=self[id]['metadata']['image_id'])
            Dockerizer.rm_network(id=self[id]['metadata']['network'])
            super().delete(id=id)
        else:
            raise KeyError(f'{colored(str(id), "cyan")} not found in store.')
