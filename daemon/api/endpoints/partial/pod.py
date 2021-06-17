from fastapi import APIRouter
from jina.helper import ArgNamespace
from jina.parsers import set_pod_parser

from ....models import DaemonID, PodModel
from ....excepts import Runtime400Exception
from ....models.partial import PartialStoreItem
from ....stores import partial_store as store

router = APIRouter(prefix='/pod', tags=['pod'])


@router.get(
    path='',
    summary='Get status of a running Pod',
    response_model=PartialStoreItem,
)
async def _status():
    return store.item


@router.post(
    path='',
    summary='Create a Pod',
    description='Create a Pod and add it to the store',
    status_code=201,
    response_model=PartialStoreItem,
)
async def _create(pod: 'PodModel'):
    try:
        args = ArgNamespace.kwargs2namespace(pod.dict(), set_pod_parser())
        return store.add(args)
    except Exception as ex:
        raise Runtime400Exception from ex


@router.delete(
    path='',
    summary='Terminate the running Pod',
    description='Terminate a running Pod and release its resources',
)
async def _delete():
    try:
        store.delete()
    except Exception as ex:
        raise Runtime400Exception from ex


@router.on_event('shutdown')
def _shutdown():
    store.delete()
