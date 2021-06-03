import os
import pathlib
import subprocess
from pathlib import Path
from queue import Queue
from threading import Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn import Config, Server

from jina import __version__, __resources_path__, Flow
from jina.logging.logger import JinaLogger
from jina.parsers import set_pea_parser, set_pod_parser
from jina.parsers.flow import set_flow_parser
from jina.peapods.peas import BasePea
from jina.peapods.pods.factory import PodFactory
from jina.peapods.runtimes import ZEDRuntime
from .excepts import (
    RequestValidationError,
    Runtime400Exception,
    daemon_runtime_exception_handler,
    validation_exception_handler,
)
from .parser import get_main_parser, _get_run_args, get_partial_parser

jinad_args = get_main_parser().parse_args([])
daemon_logger = JinaLogger('DAEMON', **vars(jinad_args))

__task_queue__ = Queue()
__dockerhost__ = 'host.docker.internal'
__root_workspace__ = jinad_args.workspace
__rootdir__ = str(Path(__file__).parent.parent.absolute())
__dockerfiles__ = str(Path(__file__).parent.absolute() / 'Dockerfiles')


def _get_app(mode=None):
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
    app.add_exception_handler(Runtime400Exception, daemon_runtime_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    if mode is None:
        app.include_router(logs.router)
        app.include_router(peas.router)
        app.include_router(pods.router)
        app.include_router(flows.router)
        app.include_router(workspaces.router)
        app.openapi_tags.extend(
            [
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
            ]
        )
    elif mode == 'pod':
        app.include_router(pods.router)
        app.openapi_tags.append(
            {
                'name': 'pods',
                'description': 'API to manage Pods',
            }
        )
    elif mode == 'pea':
        app.include_router(peas.router)
        app.openapi_tags.append(
            {
                'name': 'peas',
                'description': 'API to manage Peas',
            },
        )
    elif mode == 'flow':
        app.include_router(flows.router)
        app.openapi_tags.append(
            {
                'name': 'flows',
                'description': 'API to manage Flows',
            }
        )

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
    cfg = os.path.join(__resources_path__, 'fluent.conf')
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


def _start_consumer():
    from .tasks import ConsumerThread

    ConsumerThread().start()


def partial():
    """ Entrypoint for partial jinad. Starts one of [flow, pod, pea] """
    parser = get_partial_parser()
    args, extra_args = parser.parse_known_args()

    if args.mode == 'flow':
        flow = Flow(set_flow_parser().parse_args(extra_args))
        flow.start()
    elif args.mode == 'pod':
        pod = PodFactory.build_pod(set_pod_parser().parse_args(extra_args))
        pod.start()
    elif args.mode == 'pea':
        pea = BasePea(set_pea_parser().parse_args(extra_args))
        pea.runtime_cls = ZEDRuntime
        pea.start()
    else:
        raise ValueError(f'Can not start partial JinaD with unknown mode {args.mode}')

    jinad_args.port_expose = args.rest_api_port
    _start_uvicorn(app=_get_app(mode=args.mode))


def main():
    """Entrypoint for jinad"""
    global jinad_args, __root_workspace__
    jinad_args = _get_run_args()
    __root_workspace__ = jinad_args.workspace
    pathlib.Path(__root_workspace__).mkdir(parents=True, exist_ok=True)
    if not jinad_args.no_fluentd:
        Thread(target=_start_fluentd, daemon=True).start()
    _start_consumer()
    _start_uvicorn(app=_get_app())
