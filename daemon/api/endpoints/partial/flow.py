from fastapi import APIRouter

from jina.helper import ArgNamespace
from jina.parsers.flow import set_flow_parser
from ....excepts import Runtime400Exception
from ....models import FlowModel
from ....models.enums import UpdateOperation
from ....models.partial import PartialFlowItem
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
async def _create(flow: 'FlowModel', port_expose: int):
    """

    .. #noqa: DAR101
    .. #noqa: DAR201"""
    try:
        args = ArgNamespace.kwargs2namespace(flow.dict(), set_flow_parser())
        return store.add(args, port_expose)
    except Exception as ex:
        raise Runtime400Exception from ex


@router.put(
    path='',
    summary='Run an update operation on the Flow object',
    description='Types supported: "rolling_update"',
    response_model=PartialFlowItem,
)
async def _update(
    kind: UpdateOperation,
    dump_path: str,
    pod_name: str,
    shards: int = None,
):
    """

    .. #noqa: DAR101
    .. #noqa: DAR201"""
    try:
        return store.update(kind, dump_path, pod_name, shards)
    except ValueError as ex:
        raise Runtime400Exception from ex


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
        raise Runtime400Exception from ex


@router.on_event('shutdown')
def _shutdown():
    """

    .. #noqa: DAR101
    .. #noqa: DAR201"""
    store.delete()
