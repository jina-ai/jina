from fastapi import status, APIRouter

from jina import __version__ as jina_version
from jina.helper import colored, get_public_ip, get_internal_ip
from ... import daemon_logger
from ...config import server_config

common_router = APIRouter()


@common_router.on_event('startup')
async def startup():
    daemon_logger.success(f'\tWelcome to Jina daemon - the manager of distributed Jina')
    daemon_logger.success(f'\tUvicorn + FastAPI running on {server_config.HOST}:{server_config.PORT}')
    daemon_logger.success(f'\t🌐 Private address:\t' + colored(f'http://{get_internal_ip()}:{server_config.PORT}',
                                                              'cyan', attrs='underline'))
    daemon_logger.success(f'\t🌐 Public address:\t' + colored(f'http://{get_public_ip()}:{server_config.PORT}',
                                                              'cyan', attrs='underline'))


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
