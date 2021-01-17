import uuid
from typing import Union

from fastapi import APIRouter, HTTPException

from ... import Runtime400Exception
from ...helper import pod_to_namespace
from ...models import PodModel, RawPodModel
from ...models.status import StoreStatus
from ...stores import pod_store as store

router = APIRouter(prefix='/pods', tags=['pod'])


@router.get(
    path='',
    summary='Get all alive Pods in the store',
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


@router.put(
    path='',
    summary='Create a Pod',
    description='Create a Pod and add it to the store',
    status_code=201
)
async def _create(
        arguments: Union[PodModel, RawPodModel]
):
    try:
        return store.add(pod_to_namespace(args=arguments))
    except Exception as ex:
        raise Runtime400Exception from ex


@router.delete(
    path='/{id}',
    summary='Terminate a running Pod',
    description='Terminate a running Pod and release its resources'
)
async def _delete(id: 'uuid.UUID'):
    try:
        del store[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')


@router.on_event('shutdown')
def _shutdown():
    store.clear()
