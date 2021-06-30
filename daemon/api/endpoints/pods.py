import requests
from fastapi import Depends, APIRouter, HTTPException

from ..dependencies import PodDepends
from ... import Runtime400Exception
from ...models import DaemonID, ContainerItem, ContainerStoreStatus, PodModel
from ...stores import pod_store as store

router = APIRouter(prefix='/pods', tags=['pods'])


@router.get(
    path='', summary='Get all alive Pods\' status', response_model=ContainerStoreStatus
)
async def _get_items():
    return store.status


@router.get(path='/arguments', summary='Get all accepted arguments of a Pod')
async def _fetch_pod_params():
    return PodModel.schema()['properties']


@router.post(
    path='',
    summary='Create a Pod',
    description='Create a Pod and add it to the store',
    status_code=201,
    response_model=DaemonID,
)
async def _create(pod: PodDepends = Depends(PodDepends)):
    try:
        return store.add(
            id=pod.id,
            workspace_id=pod.workspace_id,
            params=pod.params,
            ports=pod.ports,
        )
    except Exception as ex:
        raise Runtime400Exception from ex


@router.delete(
    path='',
    summary='Terminate all running Pods',
)
async def _clear_all():
    store.clear()


@router.delete(
    path='/{id}',
    summary='Terminate a running Pod',
    description='Terminate a running Pod and release its resources',
)
async def _delete(id: DaemonID, workspace: bool = False):
    try:
        store.delete(id=id, workspace=workspace)
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')


@router.get(
    path='/{id}', summary='Get status of a running Pod', response_model=ContainerItem
)
async def _status(id: DaemonID):
    try:
        return store[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')


@router.put(path='/{id}/rolling_update', summary='Trigger a rolling update on this Pod')
async def _rolling_update(id: DaemonID, dump_path: str):
    try:
        return requests.put(
            f'{store[id].metadata.rest_api_uri}/pod/rolling_update',
            params={'dump_path': dump_path},
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')
