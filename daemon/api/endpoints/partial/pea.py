from fastapi import APIRouter

from jina.helper import ArgNamespace
from jina.parsers import set_pea_parser

from ....models import PeaModel
from ....models.partial import PartialStoreItem
from ....excepts import PartialDaemon400Exception
from ....stores import partial_store as store

router = APIRouter(prefix='/pea', tags=['pea'])


@router.get(
    path='', summary='Get status of a running Pea', response_model=PartialStoreItem
)
async def _status():
    """

    .. #noqa: DAR101
    .. #noqa: DAR201"""
    return store.item


@router.post(
    path='',
    summary='Create a Pea',
    description='Create a Pea and add it to the store',
    status_code=201,
    response_model=PartialStoreItem,
)
async def _create(pea: 'PeaModel'):
    """

    .. #noqa: DAR101
    .. #noqa: DAR201"""
    try:
        args = ArgNamespace.kwargs2namespace(pea.dict(), set_pea_parser())
        return store.add(args)
    except Exception as ex:
        raise PartialDaemon400Exception from ex


@router.delete(
    path='',
    summary='Terminate the running Pea',
    description='Terminate a running Pea and release its resources',
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
