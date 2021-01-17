from typing import List

from fastapi import APIRouter, File, UploadFile

from jina.helper import get_public_ip, get_internal_ip, get_full_version
from jina.logging.profile import used_memory_readable
from ...helper import create_meta_files_from_upload
from ...stores import pea_store, pod_store, flow_store

router = APIRouter(tags=['daemon'])


@router.on_event('startup')
async def startup():
    from ... import daemon_logger, jinad_args
    daemon_logger.info(f'''
Welcome to Jina daemon - the manager of distributed Jina
💬 Swagger UI:\thttp://localhost:8000/docs
📚 Docs address:\thttp://localhost:8000/redoc
🔒 Private address:\thttp://{get_internal_ip()}:{jinad_args.port_expose}
🌐 Public address:\thttp://{get_public_ip()}:{jinad_args.port_expose}
    ''')


@router.get(
    path='/',
)
async def _home():
    """
    The instruction HTML when user visits `/` directly
    """
    return {}


@router.get(
    path='/status',
    summary='Get the status of the daemon',
)
async def _status():
    """
    Used to check if the api is running (returns 200 & jina version)
    """
    return {
        'jina': get_full_version(),
        'peas': pea_store.status,
        'pods': pod_store.status,
        'flows': flow_store.status,
        'used_memory': used_memory_readable()
    }


@router.put(
    path='/upload',
    summary='Upload YAML & py_modules file dependencies',
)
async def _upload(
        uses_files: List[UploadFile] = File(()),
        pymodules_files: List[UploadFile] = File(())
):
    if uses_files:
        [create_meta_files_from_upload(current_file) for current_file in uses_files]

    if pymodules_files:
        [create_meta_files_from_upload(current_file) for current_file in pymodules_files]
