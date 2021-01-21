import json
import os
import subprocess
import threading

import pkg_resources
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import Config, Server

from daemon.excepts import Runtime400Exception, daemon_runtime_exception_handler
from jina import __version__
from jina.logging import JinaLogger
from .parser import get_main_parser, _get_run_args

jinad_args = get_main_parser().parse_args([])
daemon_logger = JinaLogger('DAEMON', **vars(jinad_args))



def _get_app():
    from .api.endpoints import router, flow, pod, pea, logs, workspace
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
    app.include_router(router)
    app.include_router(logs.router)
    app.include_router(pea.router)
    app.include_router(pod.router)
    app.include_router(flow.router)
    app.include_router(workspace.router)
    app.add_exception_handler(Runtime400Exception, daemon_runtime_exception_handler)

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
    daemon_logger.info('starting fluentd...')
    cfg = pkg_resources.resource_filename('jina', 'resources/fluent.conf')
    try:
        fluentd_proc = subprocess.Popen(['fluentd', '-c', cfg], stdout=subprocess.PIPE, stdin=subprocess.PIPE,
                                        bufsize=0, universal_newlines=True)
        for line in fluentd_proc.stdout:
            daemon_logger.info(f'fluentd: {line.strip()}')
    except FileNotFoundError:
        daemon_logger.warning('Fluentd not found locally, Jinad cannot stream logs!')
        jinad_args.no_fluentd = True


def main():
    global jinad_args
    jinad_args = _get_run_args()
    if not jinad_args.no_fluentd:
        threading.Thread(target=_start_fluentd, daemon=True).start()
    _start_uvicorn(app=_get_app())
