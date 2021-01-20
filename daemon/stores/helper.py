import os
import uuid
from typing import Union

from daemon import jinad_args


def get_workspace_path(workspace_id: Union[uuid.UUID, str]):
    return os.path.join(jinad_args.workspace, str(workspace_id))
