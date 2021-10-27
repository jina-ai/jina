from fastapi import Depends, APIRouter, HTTPException

from ... import Runtime400Exception
from ..dependencies import PeaDepends
from ...models import DaemonID, ContainerItem, ContainerStoreStatus, PeaModel
from ...stores import pea_store as store

router = APIRouter(prefix='/peas', tags=['peas'])


@router.get(
    path='', summary='Get all alive Pea\' status', response_model=ContainerStoreStatus
)
async def _get_items():
    return store.status


@router.get(
    path='/arguments',
    summary='Get all accepted arguments of a Pea',
)
async def _fetch_pea_params():
    return PeaModel.schema()['properties']


@router.post(
    path='',
    summary='Create a Pea',
    description='Create a Pea and add it to the store',
    status_code=201,
    response_model=DaemonID,
)
async def _create(pea: PeaDepends = Depends(PeaDepends)):
    try:
        return await store.add(
            id=pea.id,
            workspace_id=pea.workspace_id,
            params=pea.params,
            ports=pea.ports,
            envs=pea.envs,
            device_requests=pea.device_requests,
        )
    except Exception as ex:
        raise Runtime400Exception from ex


# order matters! this must be put in front of del {id}
#  https://fastapi.tiangolo.com/tutorial/path-params/?h=+path#order-matters
@router.delete(
    path='',
    summary='Terminate all running Peas',
)
async def _clear_all():
    await store.clear()


@router.delete(
    path='/{id}',
    summary='Terminate a running Pea',
    description='Terminate a running Pea and release its resources',
)
async def _delete(id: DaemonID, workspace: bool = False):
    try:
        await store.delete(id=id, workspace=workspace)
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in store')


@router.get(
    path='/{id}', summary='Get status of a running Pea', response_model=ContainerItem
)
async def _status(id: DaemonID):
    try:
        return store[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in pea store')
