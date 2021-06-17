from fastapi import APIRouter

from ....models import DaemonID
from ....models.enums import UpdateOperation
from ....models.partial import PartialFlowItem
from ....excepts import Runtime400Exception
from ....stores import partial_store as store

router = APIRouter(prefix='/flow', tags=['flow'])


@router.get(
    path='', summary='Get the status of a running Flow', response_model=PartialFlowItem
)
async def _status():
    return store.item


@router.post(
    path='',
    summary='Create a Flow from a YAML config',
    status_code=201,
    response_model=PartialFlowItem,
)
async def _create(filename: str, id: DaemonID, port_expose: int):
    try:
        return store.add(filename, id, port_expose)
    except Exception as ex:
        raise Runtime400Exception from ex


@router.put(
    path='',
    summary='Run an update operation on the Flow object',
    description='Types supported: "rolling_update" and "dump"',
    response_model=PartialFlowItem,
)
def update(
    kind: UpdateOperation,
    dump_path: str,
    pod_name: str,
    shards: int = None,
):
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
    try:
        store.delete()
    except Exception as ex:
        raise Runtime400Exception from ex


@router.on_event('shutdown')
def _shutdown():
    store.delete()
