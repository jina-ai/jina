from fastapi import APIRouter

from jina.helper import ArgNamespace
from jina.parsers import set_pod_parser
from ....excepts import PartialDaemon400Exception
from ....models import PodModel
from ....models.partial import PartialStoreItem
from ....stores import partial_store as store

router = APIRouter(prefix='/pod', tags=['pod'])


@router.get(
    path='',
    summary='Get status of a running Pod',
    response_model=PartialStoreItem,
)
async def _status():
    """

    .. #noqa: DAR101
    .. #noqa: DAR201"""
    return store.item


@router.post(
    path='',
    summary='Create a Pod',
    description='Create a Pod and add it to the store',
    status_code=201,
    response_model=PartialStoreItem,
)
async def _create(pod: 'PodModel'):
    """

    .. #noqa: DAR101
    .. #noqa: DAR201"""
    try:
        args = ArgNamespace.kwargs2namespace(pod.dict(), set_pod_parser())
        return store.add(args)
    except Exception as ex:
        raise PartialDaemon400Exception from ex


@router.delete(
    path='',
    summary='Terminate the running Pod',
    description='Terminate a running Pod and release its resources',
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
