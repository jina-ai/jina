import uuid

from fastapi import APIRouter

from .base import del_from_store, clear_store, add_store
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
    return add_store(store, pea_to_namespace(args=arguments))


@router.delete(
    path='/{id}',
    summary='Terminate a running Pea',
    description='Terminate a running Pea and release its resources'
)
async def _delete(id: 'uuid.UUID'):
    return del_from_store(store, id)


@router.on_event('shutdown')
def _shutdown():
    return clear_store(store)
