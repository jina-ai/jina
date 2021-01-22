from fastapi import APIRouter

from jina.helper import get_public_ip, get_internal_ip, get_full_version
from jina.logging.profile import used_memory_readable
from ...models.status import DaemonStatus
from ...stores import pea_store, pod_store, flow_store, workspace_store

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
        'workspaces': workspace_store.status,
        'used_memory': used_memory_readable()
    }
