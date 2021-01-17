import uuid

from fastapi import APIRouter, HTTPException

from ...helper import pea_to_namespace
from ...models import PeaModel
from ...stores import pea_store as store

router = APIRouter(prefix='/pea', tags=['pea'])


@router.get(
    path='/arguments',
    summary='Get all accept arguments of a Pea'
)
async def _fetch_pea_params():
    return PeaModel.schema()['properties']


@router.put(
    path='/',
    summary='Create a Pea',
    description='Create a Pea and add it to the store',
    status_code=201
)
async def _create(arguments: PeaModel):
    try:
        return store.add(pea_to_namespace(args=arguments))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'{e!r}')


@router.delete(
    path='/{id}',
    summary='Terminate a running Pea',
    description='Terminate a running Pea and release its resources'
)
async def _delete(id: 'uuid.UUID'):
    try:
        del store[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')


@router.on_event('shutdown')
def _shutdown():
    store.clear()
