from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException

from ... import Runtime400Exception
from ..dependencies import WorkspaceDepends
from ...stores import workspace_store as store
from ...models import DaemonID, WorkspaceItem, WorkspaceStoreStatus

router = APIRouter(prefix='/workspaces', tags=['workspaces'])


@router.get(
    path='',
    summary='Get all existing Workspaces\' status',
    response_model=WorkspaceStoreStatus,
)
async def _get_items():
    return store.status


@router.delete(
    path='',
    summary='Deleting all Workspaces',
)
async def _clear_all():
    store.clear()


@router.delete(
    path='/{id}',
    summary='Deleting an existing Workspace',
)
async def _delete(id: DaemonID, container_only: bool = False):
    try:
        if container_only:
            return store.delete_container_only(id=id)
        else:
            return store.delete(id=id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')
    except ValueError:
        raise HTTPException(
            status_code=404, detail=f'There is no container to kill in {store!r}'
        )


@router.post(
    path='',
    summary='Create a workspace & upload files',
    description='Return a DaemonID to the workspace, which can be used later when create Pea/Pod/Flow',
    # response_model=WorkspaceStoreStatus.items,
    status_code=201,
)
async def _create(workspace: WorkspaceDepends = Depends(WorkspaceDepends)):
    try:
        return workspace.j
    except Exception as ex:
        raise Runtime400Exception from ex


@router.put(
    path='/{id}',
    summary='Update files in a workspace',
    description='Return a DaemonID to the workspace, which can be used later when create Pea/Pod/Flow',
    response_model=DaemonID,
    status_code=200,
)
async def _update(id: DaemonID, files: List[UploadFile] = File(None)):
    try:
        return store.update(id=id, files=files)
    except Exception as ex:
        raise Runtime400Exception from ex


@router.get(
    path='/{id}',
    summary='Get the status of an existing Workspace',
    response_model=WorkspaceItem,
)
async def _list(id: DaemonID):
    try:
        return store[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in store')


# @router.on_event('shutdown')
# def _shutdown():
#     store.reset()
