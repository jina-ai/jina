import os
import pathlib
import subprocess
from pathlib import Path
from queue import Queue
from threading import Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import Config, Server

from jina import __version__, __resources_path__
from jina.logging.logger import JinaLogger
from daemon.excepts import (
    Runtime400Exception,
    RequestValidationError,
    PartialDaemon400Exception,
    daemon_runtime_exception_handler,
    partial_daemon_exception_handler,
    validation_exception_handler,
)
from daemon.parser import get_main_parser, _get_run_args

jinad_args = get_main_parser().parse_args([])
daemon_logger = JinaLogger('DAEMON', **vars(jinad_args))

__task_queue__ = Queue()
__root_workspace__ = jinad_args.workspace
__partial_workspace__ = '/workspace'
__rootdir__ = str(Path(__file__).parent.parent.absolute())
__dockerfiles__ = str(Path(__file__).parent.absolute() / 'Dockerfiles')


def _get_app(mode=None):
    from daemon.api.endpoints import router

    app = FastAPI(
        title='JinaD (Daemon)',
        description='REST interface for managing distributed Jina',
        version=__version__,
        openapi_tags=[
            {
                'name': 'daemon',
                'description': 'API to manage the Daemon',
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
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    if mode is None:
        from daemon.api.endpoints import flows, deployments, pods, logs, workspaces

        app.include_router(logs.router)
        app.include_router(pods.router)
        app.include_router(deployments.router)
        app.include_router(flows.router)
        app.include_router(workspaces.router)
        app.add_exception_handler(Runtime400Exception, daemon_runtime_exception_handler)
        app.openapi_tags.extend(
            [
                {
                    'name': 'flows',
                    'description': 'API to manage Flows',
                },
                {
                    'name': 'deployments',
                    'description': 'API to manage Deployments',
                },
                {
                    'name': 'pods',
                    'description': 'API to manage Pods',
                },
                {
                    'name': 'logs',
                    'description': 'API to stream Logs',
                },
                {
                    'name': 'workspaces',
                    'description': 'API to manage Workspaces',
                },
            ]
        )
    elif mode == 'deployment':
        from daemon.api.endpoints.partial import deployment

        app.include_router(deployment.router)
        app.add_exception_handler(
            PartialDaemon400Exception, partial_daemon_exception_handler
        )
        app.openapi_tags.append(
            {
                'name': 'deployment',
                'description': 'API to manage a Deployment',
            }
        )
    elif mode == 'pod':
        from daemon.api.endpoints.partial import pod

        app.include_router(pod.router)
        app.add_exception_handler(
            PartialDaemon400Exception, partial_daemon_exception_handler
        )
        app.openapi_tags.append(
            {
                'name': 'pod',
                'description': 'API to manage a Pod',
            },
        )
    elif mode == 'flow':
        from daemon.api.endpoints.partial import flow

        app.include_router(flow.router)
        app.add_exception_handler(
            PartialDaemon400Exception, partial_daemon_exception_handler
        )
        app.openapi_tags.append(
            {
                'name': 'flow',
                'description': 'API to manage a Flow',
            }
        )

    return app


def _update_default_args():
    global jinad_args, __root_workspace__
    jinad_args = _get_run_args()
    __root_workspace__ = (
        __partial_workspace__ if jinad_args.mode else jinad_args.workspace
    )


def _start_consumer():
    from daemon.tasks import ConsumerThread

    ConsumerThread().start()


def _start_uvicorn(app: 'FastAPI'):
    config = Config(
        app=app,
        host=jinad_args.host,
        port=jinad_args.port,
        loop='uvloop',
        log_level='error',
    )
    server = Server(config=config)
    server.run()


def setup():
    """Setup steps for JinaD"""
    _update_default_args()
    pathlib.Path(__root_workspace__).mkdir(parents=True, exist_ok=True)
    _start_consumer()
    _start_uvicorn(app=_get_app(mode=jinad_args.mode))


def teardown():
    """Cleanup steps for JinaD"""
    from jina import __stop_msg__

    daemon_logger.success(__stop_msg__)
    daemon_logger.close()


def main():
    """Entrypoint for JinaD"""
    try:
        setup()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        daemon_logger.info(f'error while server was running {e!r}')
    finally:
        teardown()
