import uuid
from typing import Union

from fastapi import APIRouter

from .base import add_store, del_from_store, clear_store
from ...helper import pod_to_namespace
from ...models import SinglePodModel, ParallelPodModel
from ...stores import pod_store as store

router = APIRouter(prefix='/pod', tags=['pod'])


@router.get(
    path='/arguments',
    summary='Get all accept arguments of a Pod'
)
async def _fetch_pod_params():
    return SinglePodModel.schema()['properties']


@router.put(
    path='/',
    summary='Create a Pod',
    description='Create a Pod and add it to the store',
    status_code=201
)
async def _create(
        arguments: Union[SinglePodModel, ParallelPodModel]
):
    return add_store(store, pod_to_namespace(args=arguments))


@router.delete(
    path='/{id}',
    summary='Terminate a running Pod',
    description='Terminate a running Pod and release its resources'
)
async def _delete(id: 'uuid.UUID'):
    return del_from_store(store, id)


@router.on_event('shutdown')
def _shutdown():
    return clear_store(store)
