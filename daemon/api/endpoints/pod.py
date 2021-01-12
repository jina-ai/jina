import uuid
from typing import List, Union

from fastapi import status, APIRouter, File, UploadFile
from fastapi.exceptions import HTTPException

from ... import daemon_logger
from ...excepts import PodStartException
from ...helper import pod_to_namespace, create_meta_files_from_upload
from ...models import SinglePodModel, ParallelPodModel
from ...store import pod_store

router = APIRouter()


@router.get(
    path='/pod/parameters',
    summary='Fetch all params that a Pod can accept'
)
async def _fetch_pod_params():
    return SinglePodModel.schema()['properties']



@router.put(
    path='/upload',
    summary='Upload YAML & py_modules required by a Pod',
)
async def _upload(
        uses_files: List[UploadFile] = File(()),
        pymodules_files: List[UploadFile] = File(())
):
    """

    """
    upload_status = 'nothing to upload'
    if uses_files:
        [create_meta_files_from_upload(current_file) for current_file in uses_files]
        upload_status = 'uploaded'

    if pymodules_files:
        [create_meta_files_from_upload(current_file) for current_file in pymodules_files]
        upload_status = 'uploaded'

    return {
        'status_code': status.HTTP_200_OK,
        'status': upload_status
    }


@router.put(
    path='/pod',
    summary='Create a Pod',
)
async def _create(
        pod_arguments: Union[SinglePodModel, ParallelPodModel]
):
    """This is used to create a remote Pod which gets triggered either in a Flow context or via CLI

    Args: pod_arguments (SinglePodModel or RemotePodModel)
    """
    pod_arguments = pod_to_namespace(args=pod_arguments)

    with pod_store._session():
        try:
            pod_id = pod_store._create(pod_arguments=pod_arguments)
        except PodStartException as e:
            raise HTTPException(status_code=404,
                                detail=f'Pod couldn\'t get started: {e!r}')
        except Exception as e:
            daemon_logger.error(f'Got an error while creating a pod {e!r}')
            raise HTTPException(status_code=404,
                                detail=f'Something went wrong')
        return {
            'status_code': status.HTTP_200_OK,
            'pod_id': pod_id,
            'status': 'started'
        }


@router.delete(
    path='/pod',
    summary='Terminate a running Pod',
)
async def _delete(
        pod_id: uuid.UUID
):
    """Close Pod Context
    """
    with pod_store._session():
        try:
            pod_store._delete(pod_id=pod_id)
            return {
                'status_code': status.HTTP_200_OK
            }
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Pod ID {pod_id} not found! Please create a new Pod')


@router.on_event('shutdown')
def _shutdown():
    with pod_store._session():
        pod_store._delete_all()
