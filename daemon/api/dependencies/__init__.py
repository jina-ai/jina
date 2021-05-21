from pathlib import Path
from pydantic import FilePath
from fastapi import HTTPException
from jina.helper import ArgNamespace
from pydantic.errors import PathNotAFileError

from ...stores.helper import get_workspace_path
from ...models import DaemonID, FlowModel, PodModel, PeaModel


class FlowDepends:
    def __init__(self, workspace_id: DaemonID, filename: str) -> None:
        self.workspace_id = workspace_id
        self.filename = filename
        self.validate()
        self.id = DaemonID('jflow')
        self.params = FlowModel(uses=self.filename,
                                workspace_id=self.workspace_id.jid,
                                identity=self.id.jid)

    @property
    def command(self) -> str:
        return f'jina flow --uses /workspace/{self.params.uses} ' \
               f'--identity {self.params.identity} ' \
               f'--workspace-id {self.params.workspace_id}'

    def validate(self):
        try:
            FilePath.validate(Path(get_workspace_path(self.workspace_id, self.filename)))
        except PathNotAFileError as e:
            raise HTTPException(status_code=404,
                                detail=f'File `{self.filename}` not found in workspace `{self.workspace_id}`')


class PeaDepends:
    def __init__(self, workspace_id: DaemonID, pea: PeaModel):
        self.workspace_id = workspace_id
        self.pea = pea
        self.id = DaemonID('jpea')

    @property
    def command(self) -> str:
        return f'jina pea {" ".join(ArgNamespace.kwargs2list(self.pea.dict(exclude={"log_config"})))}'

    def validate(self):
        self.pea.workspace_id = self.workspace_id
        self.pea.log_config = ''


class PodDepends:
    def __init__(self, workspace_id: DaemonID, pod: PodModel):
        self.workspace_id = workspace_id
        self.pod = pod
        self.id = DaemonID('jpod')

    @property
    def command(self) -> str:
        return f'jina pod {" ".join(ArgNamespace.kwargs2list(self.pod.dict(exclude={"log_config"})))}'
