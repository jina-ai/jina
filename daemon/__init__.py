import json
import subprocess
import threading
from collections import namedtuple

import pkg_resources
from fastapi import FastAPI
from uvicorn import Config, Server

from jina.logging import JinaLogger
from .parser import get_main_parser

daemon_logger = JinaLogger(context='👻 JINAD')


def _get_app():
    from .api.endpoints import common_router, flow, pod, pea, logs
    from .config import jinad_config, fastapi_config, server_config, openapitags_config

    context = namedtuple('context', ['router', 'openapi_tags', 'tags'])
    _all_routers = {
        'flow': context(router=flow.router,
                        openapi_tags=openapitags_config.FLOW_API_TAGS,
                        tags=[openapitags_config.FLOW_API_TAGS[0]['name']]),
        'pod': context(router=pod.router,
                       openapi_tags=openapitags_config.POD_API_TAGS,
                       tags=[openapitags_config.POD_API_TAGS[0]['name']]),
        'pea': context(router=pea.router,
                       openapi_tags=openapitags_config.PEA_API_TAGS,
                       tags=[openapitags_config.PEA_API_TAGS[0]['name']])
    }
    app = FastAPI(
        title=fastapi_config.NAME,
        description=fastapi_config.DESCRIPTION,
        version=fastapi_config.VERSION
    )
    app.include_router(router=common_router,
                       prefix=fastapi_config.PREFIX)
    app.include_router(router=logs.router,
                       prefix=fastapi_config.PREFIX)
    if jinad_config.CONTEXT == 'all':
        for _current_router in _all_routers.values():
            app.include_router(router=_current_router.router,
                               tags=_current_router.tags,
                               prefix=fastapi_config.PREFIX)
    else:
        _current_router = _all_routers[jinad_config.CONTEXT]
        app.openapi_tags = _current_router.openapi_tags
        app.include_router(router=_current_router.router,
                           tags=_current_router.tags,
                           prefix=fastapi_config.PREFIX)
    return app


def _write_openapi_schema(filename='schema.json'):
    app = _get_app()
    schema = app.openapi()
    with open(filename, 'w') as f:
        json.dump(schema, f)


def _start_uvicorn(app: 'FastAPI'):
    from .config import server_config
    config = Config(app=app,
                    host=server_config.HOST,
                    port=server_config.PORT,
                    loop='uvloop',
                    log_level='error')
    server = Server(config=config)
    server.run()
    daemon_logger.info('bye!')


def _start_fluentd():
    daemon_logger.info('starting fluentd')
    cfg = pkg_resources.resource_filename('jina', 'resources/fluent.conf')
    subprocess.Popen(['fluentd', '-c', cfg])


def _parse_arg():
    from .config import server_config
    args = get_main_parser().parse_args()
    server_config.HOST = args.host
    server_config.PORT = args.port_expose


def main():
    _parse_arg()
    threading.Thread(target=_start_fluentd).start()
    _start_uvicorn(app=_get_app())
