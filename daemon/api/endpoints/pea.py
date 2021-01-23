import uuid

from fastapi import APIRouter, HTTPException

from jina.helper import ArgNamespace
from jina.parsers import set_pea_parser
from ... import Runtime400Exception
from ...models import PeaModel
from ...models.status import StoreStatus, StoreItemStatus
from ...stores import pea_store as store

router = APIRouter(prefix='/peas', tags=['peas'])


@router.get(
    path='',
    summary='Get all alive Pea\' status',
    response_model=StoreStatus
)
async def _get_items():
    return store.status


@router.get(
    path='/arguments',
    summary='Get all accept arguments of a Pea',
)
async def _fetch_pea_params():
    return PeaModel.schema()['properties']


@router.post(
    path='',
    summary='Create a Pea',
    description='Create a Pea and add it to the store',
    status_code=201,
    response_model=uuid.UUID
)
async def _create(pea: 'PeaModel'):
    try:
        args = ArgNamespace.kwargs2namespace(pea.dict(), set_pea_parser())
        return store.add(args)
    except Exception as ex:
        raise Runtime400Exception from ex


# order matters! this must be put in front of del {id}
#  https://fastapi.tiangolo.com/tutorial/path-params/?h=+path#order-matters
@router.delete(
    path='/all',
    summary='Terminate all running Peas',
)
async def _clear_all():
    store.clear()


@router.delete(
    path='/{id}',
    summary='Terminate a running Pea',
    description='Terminate a running Pea and release its resources'
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
    summary='Get status of a running Pea',
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
