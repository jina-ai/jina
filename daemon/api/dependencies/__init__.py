from jina import Flow
from typing import Dict
from pathlib import Path
from pydantic import FilePath
from fastapi import HTTPException
from jina.helper import ArgNamespace
from pydantic.errors import PathNotAFileError

from ...models import DaemonID, FlowModel, PodModel, PeaModel
from ...helper import get_workspace_path, port_fields_from_pydantic


class FlowDepends:
    def __init__(self, workspace_id: DaemonID, filename: str) -> None:
        self.workspace_id = workspace_id
        self.filename = filename
        self.localpath = self.validate()
        self.id = DaemonID('jflow')
        self.params = FlowModel(
            uses=self.filename, workspace_id=self.workspace_id.jid, identity=self.id.jid
        )

    @property
    def command(self) -> str:
        return (
            f'jina flow --uses /workspace/{self.params.uses} '
            f'--identity {self.params.identity} '
            f'--workspace-id {self.params.workspace_id}'
        )

    @property
    def ports(self) -> Dict[str, str]:
        # TODO: Super ugly way of knowing, if the yaml file has port_expose set
        f = Flow.load_config(str(self.localpath))
        port_expose = f._common_kwargs.get('port_expose')
        # TODO: How to set port_expose which starting a Flow via CLI
        return {f'{port_expose}/tcp': port_expose} if port_expose else {}

    def validate(self):
        try:
            return FilePath.validate(
                Path(get_workspace_path(self.workspace_id, self.filename))
            )
        except PathNotAFileError as e:
            raise HTTPException(
                status_code=404,
                detail=f'File `{self.filename}` not found in workspace `{self.workspace_id}`',
            )


class PeaDepends:
    _kind = 'pea'

    def __init__(self, workspace_id: DaemonID, pea: PeaModel):
        # Deepankar: adding quotes around PeaModel breaks things
        self.workspace_id = workspace_id
        self.params = pea
        self.validate()
        self.id = DaemonID('jpea')

    @property
    def command(self) -> str:
        return f'jina {self._kind} {" ".join(ArgNamespace.kwargs2list(self.params.dict(exclude={"log_config"})))}'

    @property
    def ports(self) -> Dict:
        print(self.params)
        # TODO: Hacky way of knowing the `port` args
        return {
            f'{port}/tcp': port
            for port in port_fields_from_pydantic(self.params).values()
        }

    def validate(self):
        self.params.workspace_id = self.workspace_id
        self.params.log_config = ''


class PodDepends(PeaDepends):
    def __init__(self, workspace_id: DaemonID, pod: PodModel):
        self.workspace_id = workspace_id
        self.params = pod
        self.validate()
        self.id = DaemonID('jpod')
