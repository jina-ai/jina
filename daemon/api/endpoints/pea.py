import uuid
from typing import List

from fastapi import status, APIRouter, File, UploadFile
from fastapi.exceptions import HTTPException

from ... import daemon_logger
from ...excepts import PeaStartException
from ...helper import pea_to_namespace, create_meta_files_from_upload
from ...models import PeaModel
from ...store import pea_store

router = APIRouter()


@router.put(
    path='/pea/upload',
    summary='Upload YAML & py_modules required by a Pea',
)
async def _upload(
        uses_files: List[UploadFile] = File(()),
        pymodules_files: List[UploadFile] = File(())
):
    """
    """
    # TODO: This is repetitive code. needs refactoring
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
    path='/pea',
    summary='Create a Pea',
)
async def _create(
        pea_arguments: PeaModel
):
    """
    Used to create a Remote Pea
    """
    pea_arguments = pea_to_namespace(args=pea_arguments)

    with pea_store._session():
        try:
            pea_id = pea_store._create(pea_arguments=pea_arguments)
        except PeaStartException as e:
            raise HTTPException(status_code=404,
                                detail=f'Pea couldn\'t get started:  {e!r}')
        except Exception as e:
            daemon_logger.error(f'Got an error while creating a pea {e!r}')
            raise HTTPException(status_code=404,
                                detail=f'Something went wrong')
    return {
        'status_code': status.HTTP_200_OK,
        'pea_id': pea_id,
        'status': 'started'
    }


@router.delete(
    path='/pea',
    summary='Terminate a running Pea',
)
async def _delete(
        pea_id: uuid.UUID
):
    """Close Pea Context
    """
    with pea_store._session():
        try:
            pea_store._delete(pea_id=pea_id)
            return {
                'status_code': status.HTTP_200_OK
            }
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Pea ID {pea_id} not found! Please create a new Pea')


@router.on_event('shutdown')
def _shutdown():
    with pea_store._session():
        pea_store._delete_all()
