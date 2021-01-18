import os
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File

from jina.helper import get_public_ip, get_internal_ip, get_full_version
from jina.logging.profile import used_memory_readable
from ... import jinad_args
from ...models.status import DaemonStatus
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
    response_model=DaemonStatus
)
async def _status():
    _info = get_full_version()
    return {
        'jina': _info[0],
        'envs': _info[1],
        'peas': pea_store.status,
        'pods': pod_store.status,
        'flows': flow_store.status,
        'used_memory': used_memory_readable()
    }


@router.post(
    path='/upload',
    summary='Upload dependencies into a workspace',
    description='Return a UUID to the workspace, which can be used later when create Pea/Pod/Flow',
    response_model=uuid.UUID
)
async def _upload(files: List[UploadFile] = File(())):
    _id = uuid.uuid1()
    _workdir = os.path.join(jinad_args.workspace, str(_id))
    Path(_workdir).mkdir(parents=True, exist_ok=False)
    for f in files:
        with open(os.path.join(_workdir, f.filename), 'wb') as fp:
            content = f.file.read()
            fp.write(content)
    return _id
