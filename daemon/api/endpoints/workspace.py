import uuid
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException

from ... import Runtime400Exception
from ...models.status import StoreStatus, StoreItemStatus
from ...stores import workspace_store as store

router = APIRouter(prefix='/workspaces', tags=['workspaces'])


@router.get(
    path='',
    summary='Get all existing Workspaces\' status',
    response_model=StoreStatus
)
async def _get_items():
    return store.status


@router.delete(
    path='/all',
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
        del store[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')


@router.post(
    path='',
    summary='Create a Workspace and upload files to it',
    description='Return a UUID to the workspace, which can be used later when create Pea/Pod/Flow',
    response_model=uuid.UUID,
    status_code=201,
)
async def _create(files: List[UploadFile] = File(...)):
    try:
        return store.add(files)
    except Exception as ex:
        raise Runtime400Exception from ex


@router.get(
    path='/{id}',
    summary='Get the status of an existing Workspace',
    response_model=StoreItemStatus
)
async def _list(id: uuid.UUID):
    try:
        return store[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')


@router.on_event('shutdown')
def _shutdown():
    store.reset()
