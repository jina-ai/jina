import json
import os
import subprocess
import threading

import pkg_resources
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import Config, Server

from jina import __version__
from jina.logging import JinaLogger
from .parser import get_main_parser, _get_run_args

daemon_logger = JinaLogger(context='👻',
                           log_config=os.getenv('JINAD_LOG_CONFIG',
                                                pkg_resources.resource_filename(
                                                    'jina', '/'.join(('resources', 'logging.daemon.yml')))))

jinad_args = None  # type: 'Namespace'


def _get_app():
    from .api.endpoints import router, flow, pod, pea, logs
    app = FastAPI(
        titl='JinaD (Daemon)',
        description='The REST API of the daemon for managing distributed Jina',
        version=__version__,

        openapi_tags=[
            {
                'name': 'daemon',
                'description': 'API to manage Daemon',
            },
            {
                'name': 'flow',
                'description': 'API to manage Flows',
            },
            {
                'name': 'pod',
                'description': 'API to manage Pods (__should be used by Flow APIs only__)',
            },
            {
                'name': 'pea',
                'description': 'API to manage Peas',
            },
            {
                'name': 'logs',
                'description': 'API to manage logs',
            }
        ],
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )
    app.include_router(router=router)
    app.include_router(router=logs.router)
    app.include_router(router=pea.router)
    app.include_router(router=pod.router)
    app.include_router(router=flow.router)

    return app


def _write_openapi_schema(filename='daemon.json'):
    app = _get_app()
    schema = app.openapi()
    with open(filename, 'w') as f:
        json.dump(schema, f)


def _start_uvicorn(app: 'FastAPI'):
    config = Config(app=app,
                    host=jinad_args.host,
                    port=jinad_args.port_expose,
                    loop='uvloop',
                    log_level='error')
    server = Server(config=config)
    server.run()
    daemon_logger.info('Goodbye!')


def _start_fluentd():
    daemon_logger.info('Starting fluentd')
    cfg = pkg_resources.resource_filename('jina', 'resources/fluent.conf')
    try:
        subprocess.Popen(['fluentd', '-qq', '-c', cfg])
    except FileNotFoundError:
        daemon_logger.warning('Fluentd not found locally, Jinad cannot stream logs!')


def main():
    global jinad_args
    jinad_args = _get_run_args()
    if not jinad_args.no_fluentd:
        threading.Thread(target=_start_fluentd, daemon=True).start()
    _start_uvicorn(app=_get_app())
