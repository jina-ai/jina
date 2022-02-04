from typing import Optional, Dict, Any

from fastapi import Depends, APIRouter, HTTPException

from daemon import Runtime400Exception
from daemon.api.dependencies import DeploymentDepends
from daemon.models import DaemonID, ContainerItem, ContainerStoreStatus, DeploymentModel
from daemon.stores import deployment_store as store

router = APIRouter(prefix='/deployments', tags=['deployments'])


@router.get(
    path='',
    summary='Get all alive Deployments\' status',
    response_model=ContainerStoreStatus,
)
async def _get_items():
    return store.status


@router.get(path='/arguments', summary='Get all accepted arguments of a Deployment')
async def _fetch_deployment_params():
    return DeploymentModel.schema()['properties']


@router.post(
    path='',
    summary='Create a Deployment',
    description='Create a Deployment and add it to the store',
    status_code=201,
    response_model=DaemonID,
)
async def _create(deployment: DeploymentDepends = Depends(DeploymentDepends)):
    try:
        return await store.add(
            id=deployment.id,
            workspace_id=deployment.workspace_id,
            params=deployment.params,
            ports=deployment.ports,
            envs=deployment.envs,
            device_requests=deployment.device_requests,
        )
    except Exception as ex:
        raise Runtime400Exception from ex


@router.put(
    path='/rolling_update/{id}',
    summary='Trigger a rolling_update operation on the Deployment object',
)
async def _rolling_update(
    id: DaemonID,
    uses_with: Optional[Dict[str, Any]] = None,
):
    try:
        return await store.rolling_update(id=id, uses_with=uses_with)
    except Exception as ex:
        raise Runtime400Exception from ex


@router.put(
    path='/scale/{id}',
    summary='Trigger a scale operation on the Deployment object',
)
async def _scale(id: DaemonID, replicas: int):
    try:
        return await store.scale(id=id, replicas=replicas)
    except Exception as ex:
        raise Runtime400Exception from ex


@router.delete(
    path='',
    summary='Terminate all running Deployments',
)
async def _clear_all():
    await store.clear()


@router.delete(
    path='/{id}',
    summary='Terminate a running Deployment',
    description='Terminate a running Deployment and release its resources',
)
async def _delete(id: DaemonID, workspace: bool = False):
    try:
        await store.delete(id=id, workspace=workspace)
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in store')


@router.get(
    path='/{id}',
    summary='Get status of a running Deployment',
    response_model=ContainerItem,
)
async def _status(id: DaemonID):
    try:
        return store[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in store')
