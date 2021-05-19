from fastapi import APIRouter, File, UploadFile, Body
from fastapi.exceptions import HTTPException
from pydantic.types import FilePath
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_200_OK

from ... import Runtime400Exception
from ...models import DaemonID, ContainerItem, ContainerStoreStatus, FlowModel, UpdateOperationEnum
from ...stores import flow_store as store

router = APIRouter(prefix='/flows', tags=['flows'])


@router.get(
    path='',
    summary='Get all alive Flows\' status',
    response_model=ContainerStoreStatus
)
async def _get_items():
    return store.status


@router.get(path='/arguments', summary='Get all accept arguments of a Flow')
async def _fetch_flow_params():
    return FlowModel.schema()['properties']


@router.post(
    path='',
    summary='Create a Flow from a YAML config',
    status_code=201,
    response_model=DaemonID,
)
async def _create(workspace_id: DaemonID, filename: str):
    try:

        return store.add(filename=filename, workspace_id=workspace_id)
    except Exception as ex:
        raise Runtime400Exception from ex


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


# @router.on_event('shutdown')
# def _shutdown():
#     store.reset()
