from fastapi import status, APIRouter

from jina import __version__ as jina_version
from jina.logging import JinaLogger
from ...config import server_config

logger = JinaLogger(context='👻 JINAD')
common_router = APIRouter()


@common_router.on_event('startup')
async def startup():
    logger.success(f'Uvicorn + FastAPI running on {server_config.HOST}:{server_config.PORT}')
    logger.success('Welcome to Jina daemon - the remote manager for jina!')


@common_router.get(
    path='/alive',
    summary='Get status of jinad',
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
