from fastapi import APIRouter
from jina.helper import ArgNamespace
from jina.parsers import set_pea_parser

from ....models import DaemonID, PeaModel
from ....excepts import Runtime400Exception
from ....models.partial import PartialStoreItem
from ....stores import partial_store as store

router = APIRouter(prefix='/pea', tags=['pea'])


@router.get(
    path='', summary='Get status of a running Pea', response_model=PartialStoreItem
)
async def _status():
    return store.status


@router.post(
    path='',
    summary='Create a Pea',
    description='Create a Pea and add it to the store',
    status_code=201,
    response_model=DaemonID,
)
async def _create(pea: 'PeaModel'):
    try:
        args = ArgNamespace.kwargs2namespace(pea.dict(), set_pea_parser())
        return store.add(args)
    except Exception as ex:
        raise Runtime400Exception from ex


@router.delete(
    path='',
    summary='Terminate the running Pea',
    description='Terminate a running Pea and release its resources',
)
async def _delete():
    try:
        store.delete()
    except Exception as ex:
        raise Runtime400Exception from ex


@router.on_event('shutdown')
def _shutdown():
    store.delete()
