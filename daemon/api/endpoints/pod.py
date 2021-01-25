import uuid

from fastapi import APIRouter, HTTPException

from jina.helper import ArgNamespace
from jina.parsers import set_pod_parser
from ... import Runtime400Exception
from ...models import PodModel
from ...models.status import StoreStatus, StoreItemStatus
from ...stores import pod_store as store

router = APIRouter(prefix='/pods', tags=['pods'])


@router.get(
    path='',
    summary='Get all alive Pods\' status',
    response_model=StoreStatus
)
async def _get_items():
    return store.status


@router.get(
    path='/arguments',
    summary='Get all accept arguments of a Pod'
)
async def _fetch_pod_params():
    return PodModel.schema()['properties']


@router.post(
    path='',
    summary='Create a Pod',
    description='Create a Pod and add it to the store',
    status_code=201,
    response_model=uuid.UUID
)
async def _create(pod: 'PodModel'):
    try:
        args = ArgNamespace.kwargs2namespace(pod.dict(), set_pod_parser())
        return store.add(args)
    except Exception as ex:
        raise Runtime400Exception from ex


@router.delete(
    path='/all',
    summary='Terminate all running Pods',
)
async def _clear_all():
    store.clear()


@router.delete(
    path='/{id}',
    summary='Terminate a running Pod',
    description='Terminate a running Pod and release its resources'
)
async def _delete(
    id: uuid.UUID,
    workspace: bool = False
):
    try:
        store.delete(id=id, workspace=workspace)
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')


@router.get(
    path='/{id}',
    summary='Get status of a running Pod',
    response_model=StoreItemStatus
)
async def _status(id: uuid.UUID):
    try:
        return store[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')


@router.on_event('shutdown')
def _shutdown():
    store.reset()
