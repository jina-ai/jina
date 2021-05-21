import subprocess
import pkg_resources
from pathlib import Path
from threading import Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import Config, Server

from jina import __version__
from jina.logging import JinaLogger
from .parser import get_main_parser, _get_run_args
from .excepts import (
    RequestValidationError,
    Runtime400Exception,
    daemon_runtime_exception_handler,
    validation_exception_handler,
)

jinad_args = get_main_parser().parse_args([])
daemon_logger = JinaLogger('DAEMON', **vars(jinad_args))

__root_workspace__ = jinad_args.workspace
__rootdir__ = str(Path(__file__).parent.parent.absolute())
__dockerfiles__ = str(Path(__file__).parent.absolute() / 'Dockerfiles')


def _get_app():
    from .api.endpoints import router, flows, pods, peas, logs, workspaces

    app = FastAPI(
        title='JinaD (Daemon)',
        description='REST interface for managing distributed Jina',
        version=__version__,
        openapi_tags=[
            {
                'name': 'daemon',
                'description': 'API to manage the Daemon',
            },
            {
                'name': 'flows',
                'description': 'API to manage Flows',
            },
            {
                'name': 'pods',
                'description': 'API to manage Pods',
            },
            {
                'name': 'peas',
                'description': 'API to manage Peas',
            },
            {
                'name': 'logs',
                'description': 'API to stream Logs',
            },
            {
                'name': 'workspaces',
                'description': 'API to manage Workspaces',
            },
        ],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.include_router(router)
    app.include_router(logs.router)
    app.include_router(peas.router)
    app.include_router(pods.router)
    app.include_router(flows.router)
    app.include_router(workspaces.router)
    app.add_exception_handler(Runtime400Exception, daemon_runtime_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    return app


def _start_uvicorn(app: 'FastAPI'):
    config = Config(
        app=app,
        host=jinad_args.host,
        port=jinad_args.port_expose,
        loop='uvloop',
        log_level='error',
    )
    server = Server(config=config)
    server.run()
    from jina import __stop_msg__

    daemon_logger.success(__stop_msg__)


def _start_fluentd():
    daemon_logger.info('starting fluentd...')
    cfg = pkg_resources.resource_filename('jina', 'resources/fluent.conf')
    try:
        fluentd_proc = subprocess.Popen(
            ['fluentd', '-c', cfg],
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            bufsize=0,
            universal_newlines=True,
        )
        for line in fluentd_proc.stdout:
            daemon_logger.debug(f'fluentd: {line.strip()}')
    except FileNotFoundError:
        daemon_logger.warning('fluentd not found locally, jinad cannot stream logs!')
        jinad_args.no_fluentd = True


def main():
    """Entrypoint for jinad"""
    global jinad_args, __root_workspace__
    jinad_args = _get_run_args()
    __root_workspace__ = jinad_args.workspace
    if not jinad_args.no_fluentd:
        Thread(target=_start_fluentd, daemon=True).start()
    _start_uvicorn(app=_get_app())
