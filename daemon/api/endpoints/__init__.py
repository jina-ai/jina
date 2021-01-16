from typing import List

from fastapi import APIRouter, File, UploadFile
from fastapi import status

from jina import __version__
from jina.helper import get_public_ip, get_internal_ip
from .base import del_from_store, clear_store, add_store
from ... import daemon_logger, jinad_args
from ...helper import create_meta_files_from_upload

router = APIRouter(tags=['daemon'])


@router.on_event('startup')
async def startup():
    daemon_logger.info(f'''
Welcome to Jina daemon - the manager of distributed Jina
📚 Docs address:\thttp://localhost:8000/redoc
🔒 Private address:\thttp://{get_internal_ip()}:{jinad_args.port_expose}
🌐 Public address:\thttp://{get_public_ip()}:{jinad_args.port_expose}
    ''')


@router.get(
    path='/status',
    summary='Get the status of the daemon',
    status_code=status.HTTP_200_OK
)
async def _status():
    """
    Used to check if the api is running (returns 200 & jina version)
    """
    return {
        'status_code': status.HTTP_200_OK,
        'version': __version__
    }


@router.put(
    path='/upload',
    summary='Upload YAML & py_modules required',
)
async def _upload(
        uses_files: List[UploadFile] = File(()),
        pymodules_files: List[UploadFile] = File(())
):
    if uses_files:
        [create_meta_files_from_upload(current_file) for current_file in uses_files]

    if pymodules_files:
        [create_meta_files_from_upload(current_file) for current_file in pymodules_files]
