import uuid

from fastapi import APIRouter, File, UploadFile
from fastapi.exceptions import HTTPException

from ... import Runtime400Exception
from ...models import FlowModel
from ...models.status import FlowStoreStatus, FlowItemStatus
from ...stores import flow_store as store

router = APIRouter(prefix='/flows', tags=['flows'])


@router.get(
    path='',
    summary='Get all alive Flows\' status',
    response_model=FlowStoreStatus
)
async def _get_items():
    return store.status


@router.get(
    path='/arguments',
    summary='Get all accept arguments of a Flow'
)
async def _fetch_flow_params():
    return FlowModel.schema()['properties']


@router.put(
    path='',
    summary='Creat a Flow from a YAML config',
    status_code=201,
    response_model=uuid.UUID
)
async def _create(
        flow: UploadFile = File(...)
):
    try:
        return store.add(config=flow.file)
    except Exception as ex:
        raise Runtime400Exception from ex


@router.delete(
    path='/{id}',
    summary='Terminate a running Flow',
    description='Terminate a running Flow and release its resources'
)
async def _delete(id: 'uuid.UUID'):
    try:
        del store[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')


@router.get(
    path='/{id}',
    summary='Get the status of a running Flow',
    response_model=FlowItemStatus
)
async def _status(
        id: 'uuid.UUID',
):
    try:
        return store[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')


@router.on_event('shutdown')
def _shutdown():
    store.clear()
