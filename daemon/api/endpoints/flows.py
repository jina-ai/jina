from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException

from ..dependencies import FlowDepends
from ... import Runtime400Exception
from ...models import DaemonID, ContainerItem, ContainerStoreStatus, FlowModel
from ...models.enums import UpdateOperation
from ...stores import flow_store as store

router = APIRouter(prefix='/flows', tags=['flows'])


@router.get(
    path='', summary='Get all alive Flows\' status', response_model=ContainerStoreStatus
)
async def _get_items():
    return store.status


@router.get(path='/arguments', summary='Get all accepted arguments of a Flow')
async def _fetch_flow_params():
    return FlowModel.schema()['properties']


@router.post(
    path='',
    summary='Create a Flow from a YAML config',
    status_code=201,
    response_model=DaemonID,
)
async def _create(flow: FlowDepends = Depends(FlowDepends)):
    try:
        return store.add(
            id=flow.id,
            workspace_id=flow.workspace_id,
            params=flow.params,
            ports=flow.ports,
            port_expose=flow.port_expose,
        )
    except Exception as ex:
        raise Runtime400Exception from ex


@router.put(
    path='/{id}',
    summary='Run an update operation on the Flow object',
    description='Types supported: "rolling_update"',
)
async def _update(
    id: DaemonID,
    kind: UpdateOperation,
    dump_path: str,
    pod_name: str,
    shards: int = None,
):
    return store.update(id, kind, dump_path, pod_name, shards)


# order matters! this must be put in front of del {id}
#  https://fastapi.tiangolo.com/tutorial/path-params/?h=+path#order-matters
@router.delete(
    path='',
    summary='Terminate all running Flows',
)
async def _clear_all():
    store.clear()


@router.delete(
    path='/{id}',
    summary='Terminate a running Flow',
    description='Terminate a running Flow and release its resources',
)
async def _delete(id: DaemonID):
    try:
        store.delete(id=id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')


@router.get(
    path='/{id}',
    summary='Get the status of a running Flow',
    response_model=ContainerItem,
)
async def _status(id: DaemonID):
    try:
        return store[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in {store!r}')
