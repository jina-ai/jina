import os
from pathlib import Path


def generate_default_volume_and_workspace(workspace_id=''):
    """automatically generate a docker volume, and an Executor workspace inside it

    :param workspace_id: id that will be part of the fallback workspace path. Default is not adding such an id
    :return: List of volumes and a workspace string
    """

    default_workspace = os.environ.get('JINA_DEFAULT_WORKSPACE_BASE')
    container_addr = '/app'
    if default_workspace:  # use default workspace provided in env var
        host_addr = default_workspace
        workspace = os.path.relpath(
            path=os.path.abspath(default_workspace), start=Path.home()
        )
    else:  # fallback if no custom volume and no default workspace
        workspace = os.path.join('.jina', 'executor-workspace')
        host_addr = os.path.join(
            Path.home(),
            workspace,
            workspace_id,
        )
    workspace_in_container = os.path.join(container_addr, workspace)
    generated_volumes = [os.path.abspath(host_addr) + f':{container_addr}']
    return generated_volumes, workspace_in_container
