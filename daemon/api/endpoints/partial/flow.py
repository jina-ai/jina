from typing import Optional, Dict, Any
from fastapi import APIRouter

from jina.helper import ArgNamespace
from jina.parsers.flow import set_flow_parser

from ....models import FlowModel
from ....models.ports import PortMappings
from ....models.partial import PartialFlowItem
from ....excepts import PartialDaemon400Exception
from ....stores import partial_store as store

router = APIRouter(prefix='/flow', tags=['flow'])


@router.get(
    path='', summary='Get the status of a running Flow', response_model=PartialFlowItem
)
async def _status():
    """

    .. #noqa: DAR101
    .. #noqa: DAR201"""
    return store.item


@router.post(
    path='',
    summary='Create a Flow',
    status_code=201,
    response_model=PartialFlowItem,
)
async def _create(
    flow: 'FlowModel', ports: Optional[PortMappings] = None, envs: Optional[Dict] = {}
):
    """

    .. #noqa: DAR101
    .. #noqa: DAR201"""
    try:
        args = ArgNamespace.kwargs2namespace(flow.dict(), set_flow_parser())
        return store.add(args, ports, envs)
    except Exception as ex:
        raise PartialDaemon400Exception from ex


@router.put(
    path='/rolling_update',
    summary='Peform rolling_update on the Flow object',
    response_model=PartialFlowItem,
)
async def rolling_update(
    pod_name: str,
    uses_with: Optional[Dict[str, Any]] = None,
):
    """

    .. #noqa: DAR101
    .. #noqa: DAR201
    """
    try:
        return store.rolling_update(pod_name=pod_name, uses_with=uses_with)
    except ValueError as ex:
        raise PartialDaemon400Exception from ex


@router.put(
    path='/scale',
    summary='Scale a Pod in the running Flow',
    response_model=PartialFlowItem,
)
async def scale(pod_name: str, replicas: int):
    """

    .. #noqa: DAR101
    .. #noqa: DAR201
    """
    try:
        return store.scale(pod_name=pod_name, replicas=replicas)
    except ValueError as ex:
        raise PartialDaemon400Exception from ex


@router.delete(
    path='',
    summary='Terminate the running Flow',
    description='Terminate a running Flow and release its resources',
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
