from fastapi import APIRouter

from .... import extra_args
from ....models import FlowModel
from ....models.base import StoreItem
from ....stores import partial

router = APIRouter(prefix='/flow', tags=['flow'])
partial_flow_store: partial.FlowStore = partial.FlowStore(extra_args)


@router.get(
    path='', summary='Get the status of a running Flow', response_model=StoreItem
)
async def _status():
    return partial_flow_store.status


@router.get(path='/arguments', summary='Get all accept arguments of a Flow')
async def _fetch_flow_params():
    return FlowModel.schema()['properties']


# TODO add rolling update or other functionality of a flow here
