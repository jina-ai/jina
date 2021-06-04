from fastapi import APIRouter

from .... import extra_args
from ....models import PodModel
from ....models.base import StoreItem
from ....stores import partial

router = APIRouter(prefix='/pod', tags=['pod'])
partial_pod_store: partial.PodStore = partial.PodStore(extra_args)


@router.get(
    path='', summary='Get the status of a running Pod', response_model=StoreItem
)
async def _status():
    return partial_pod_store.status


@router.get(path='/arguments', summary='Get all accept arguments of a Pod')
async def _fetch_pod_params():
    return PodModel.schema()['properties']
