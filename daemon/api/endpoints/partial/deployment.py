from typing import Optional, Dict, Any
from fastapi import APIRouter

from jina.helper import ArgNamespace
from jina.parsers import set_deployment_parser

from daemon.excepts import PartialDaemon400Exception
from daemon.models import DeploymentModel
from daemon.models.partial import PartialStoreItem
from daemon.stores import partial_store as store

router = APIRouter(prefix='/deployment', tags=['deployment'])


@router.get(
    path='',
    summary='Get status of a running Deployment',
    response_model=PartialStoreItem,
)
async def _status():
    """

    .. #noqa: DAR101
    .. #noqa: DAR201"""
    return store.item


@router.post(
    path='',
    summary='Create a Deployment',
    description='Create a Deployment and add it to the store',
    status_code=201,
    response_model=PartialStoreItem,
)
async def _create(deployment: 'DeploymentModel', envs: Optional[Dict] = {}):
    """

    .. #noqa: DAR101
    .. #noqa: DAR201"""
    try:
        args = ArgNamespace.kwargs2namespace(deployment.dict(), set_deployment_parser())
        return store.add(args, envs)
    except Exception as ex:
        raise PartialDaemon400Exception from ex


@router.put(
    path='/rolling_update',
    summary='Run a rolling_update operation on the Deployment object',
    response_model=PartialStoreItem,
)
async def rolling_update(uses_with: Optional[Dict[str, Any]] = None):
    """

    .. #noqa: DAR101
    .. #noqa: DAR201
    """
    try:
        return await store.rolling_update(uses_with=uses_with)
    except ValueError as ex:
        raise PartialDaemon400Exception from ex


@router.put(
    path='/scale',
    summary='Run a scale operation on the Deployment object',
    response_model=PartialStoreItem,
)
async def scale(replicas: int):
    """

    .. #noqa: DAR101
    .. #noqa: DAR201
    """
    try:
        return await store.scale(replicas=replicas)
    except ValueError as ex:
        raise PartialDaemon400Exception from ex


@router.delete(
    path='',
    summary='Terminate the running Deployment',
    description='Terminate a running Deployment and release its resources',
)
async def _delete():
    """

    .. #noqa: DAR101
    .. #noqa: DAR201"""
    try:
        store.delete()
    except Exception as ex:
        raise PartialDaemon400Exception from ex


@router.on_event('shutdown')
def _shutdown():
    """

    .. #noqa: DAR101
    .. #noqa: DAR201"""
    store.delete()
