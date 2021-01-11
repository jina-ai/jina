from fastapi import status, APIRouter

from jina import __version__ as jina_version
from ... import daemon_logger
from ...config import server_config

common_router = APIRouter()


@common_router.on_event('startup')
async def startup():
    daemon_logger.success(f'Welcome to Jina daemon - the manager of distributed Jina\n'
                          f'Uvicorn + FastAPI running on {server_config.HOST}:{server_config.PORT}')


@common_router.get(
    path='/alive',
    summary='Check if daemon is alive',
    status_code=status.HTTP_200_OK
)
async def _status():
    """
    Used to check if the api is running (returns 200 & jina version)
    """
    # TODO(Deepankar): should we add versions of executors?
    return {
        'status_code': status.HTTP_200_OK,
        'jina_version': jina_version
    }
