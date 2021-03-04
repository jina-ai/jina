import uuid
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Body, HTTPException

from ... import Runtime400Exception
from ...models.status import StoreStatus, StoreItemStatus
from ...stores import workspace_store as store

router = APIRouter(prefix='/workspaces', tags=['workspaces'])


@router.get(
    path='', summary='Get all existing Workspaces\' status', response_model=StoreStatus
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
async def _delete(id: uuid.UUID):
    try:
        store.delete(id=id, everything=True)
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')


@router.post(
    path='',
    summary='Upload files to a workspace',
    description='Return a UUID to the workspace, which can be used later when create Pea/Pod/Flow',
    response_model=uuid.UUID,
    status_code=201,
)
async def _create(
    files: List[UploadFile] = File(...), workspace_id: Optional[uuid.UUID] = Body(None)
):
    try:
        return store.add(files, workspace_id)
    except Exception as ex:
        raise Runtime400Exception from ex


@router.get(
    path='/{id}',
    summary='Get the status of an existing Workspace',
    response_model=StoreItemStatus,
)
async def _list(id: uuid.UUID):
    try:
        return store[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')


@router.on_event('shutdown')
def _shutdown():
    store.reset()
