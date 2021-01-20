import os
import uuid

from daemon import jinad_args


def get_workspace_path(workspace_id: uuid.UUID):
    return os.path.join(jinad_args.workspace, str(workspace_id))
