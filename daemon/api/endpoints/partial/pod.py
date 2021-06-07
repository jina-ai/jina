from fastapi import APIRouter, HTTPException

from .... import nested_args
from ....models import PodModel
from ....models.base import StoreItem
from ....stores import partial

router = APIRouter(prefix='/pod', tags=['pod'])
partial_pod_store: partial.PodStore = partial.PodStore(nested_args)


@router.get(
    path='', summary='Get the status of a running Pod', response_model=StoreItem
)
async def _status():
    return partial_pod_store.status


@router.get(path='/arguments', summary='Get all accept arguments of a Pod')
async def _fetch_pod_params():
    return PodModel.schema()['properties']


@router.put(path='/rolling_update', summary='Trigger a rolling update on this Pod')
async def _rolling_update(dump_path: str):
    try:
        partial_pod_store.pod.rolling_update(dump_path)
    except AttributeError:
        raise HTTPException(
            status_code=405, detail=f'Pod does not support rolling update'
        )
