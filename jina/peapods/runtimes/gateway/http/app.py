import argparse
import inspect
import json
from typing import Dict

from google.protobuf.json_format import MessageToDict

from ....grpc import Grpclet
from ....zmq import AsyncZmqlet
from ..... import __version__
from .....clients.request import request_generator
from .....helper import get_full_version
from .....importer import ImportExtensions
from .....logging.logger import JinaLogger
from .....logging.profile import used_memory_readable


def get_fastapi_app(args: 'argparse.Namespace', logger: 'JinaLogger'):
    """
    Get the app from FastAPI as the REST interface.

    :param args: passed arguments.
    :param logger: Jina logger.
    :return: fastapi app
    """
    with ImportExtensions(required=True):
        from fastapi import FastAPI
        from starlette.requests import Request
        from fastapi.responses import HTMLResponse
        from fastapi.middleware.cors import CORSMiddleware
        from .models import (
            JinaStatusModel,
            JinaRequestModel,
            JinaEndpointRequestModel,
            JinaResponseModel,
            PROTO_TO_PYDANTIC_MODELS,
        )

    docs_url = '/docs'
    app = FastAPI(
        title=args.title or 'My Jina Service',
        description=args.description
        or 'This is my awesome service. You can set `title` and `description` in your `Flow` or `Gateway` '
        'to customize this text.',
        version=__version__,
        docs_url=docs_url if args.default_swagger_ui else None,
    )

    if args.cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )
        logger.warning(
            'CORS is enabled. This service is now accessible from any website!'
        )

    if args.grpc_data_requests:
        from ....stream.gateway import GrpcGatewayStreamer

        iolet = Grpclet(
            args=args,
            message_callback=None,
            logger=logger,
        )
        streamer = GrpcGatewayStreamer(args, iolet)
    else:
        from ....stream.gateway import ZmqGatewayStreamer

        iolet = AsyncZmqlet(args, logger)
        streamer = ZmqGatewayStreamer(args, iolet)

    @app.on_event('shutdown')
    async def _shutdown():
        if inspect.iscoroutinefunction(iolet.close):
            await iolet.close()
        else:
            iolet.close()

    openapi_tags = []
    if not args.no_debug_endpoints:
        openapi_tags.append(
            {
                'name': 'Debug',
                'description': 'Debugging interface. In production, you should hide them by setting '
                '`--no-debug-endpoints` in `Flow`/`Gateway`.',
            }
        )

        @app.get(
            path='/status',
            summary='Get the status of Jina service',
            response_model=JinaStatusModel,
            tags=['Debug'],
        )
        async def _status():
            """
            Get the status of this Jina service.

            This is equivalent to running `jina -vf` from command line.

            .. # noqa: DAR201
            """
            _info = get_full_version()
            return {
                'jina': _info[0],
                'envs': _info[1],
                'used_memory': used_memory_readable(),
            }

        @app.post(
            path='/post',
            summary='Post a data request to some endpoint',
            response_model=PROTO_TO_PYDANTIC_MODELS.RequestProto,
            tags=['Debug']
            # do not add response_model here, this debug endpoint should not restricts the response model
        )
        async def post(body: JinaEndpointRequestModel):
            """
            Post a data request to some endpoint.

            This is equivalent to the following:

                from jina import Flow

                f = Flow().add(...)

                with f:
                    f.post(endpoint, ...)

            .. # noqa: DAR201
            .. # noqa: DAR101
            """
            # The above comment is written in Markdown for better rendering in FastAPI

            bd = body.dict()  # type: Dict
            return await _get_singleton_result(request_generator(**bd))

    def expose_executor_endpoint(exec_endpoint, http_path=None, **kwargs):
        """Exposing an executor endpoint to http endpoint
        :param exec_endpoint: the executor endpoint
        :param http_path: the http endpoint
        :param kwargs: kwargs accepted by FastAPI
        """

        # set some default kwargs for richer semantics
        # group flow exposed endpoints into `customized` group
        kwargs['tags'] = kwargs.get('tags', ['Customized'])
        kwargs['response_model'] = kwargs.get(
            'response_model',
            JinaResponseModel,  # use standard response model by default
        )
        kwargs['methods'] = kwargs.get('methods', ['POST'])

        @app.api_route(
            path=http_path or exec_endpoint, name=http_path or exec_endpoint, **kwargs
        )
        async def foo(body: JinaRequestModel):
            bd = body.dict() if body else {'data': None}
            bd['exec_endpoint'] = exec_endpoint
            return await _get_singleton_result(request_generator(**bd))

    if not args.no_crud_endpoints:
        openapi_tags.append(
            {
                'name': 'CRUD',
                'description': 'CRUD interface. If your service does not implement those interfaces, you can should '
                'hide them by setting `--no-crud-endpoints` in `Flow`/`Gateway`.',
            }
        )
        crud = {
            '/index': {'methods': ['POST']},
            '/search': {'methods': ['POST']},
            '/delete': {'methods': ['DELETE']},
            '/update': {'methods': ['PUT']},
        }
        for k, v in crud.items():
            v['tags'] = ['CRUD']
            v[
                'description'
            ] = f'Post data requests to the Flow. Executors with `@requests(on="{k}")` will respond.'
            expose_executor_endpoint(exec_endpoint=k, **v)

    if openapi_tags:
        app.openapi_tags = openapi_tags

    if args.expose_endpoints:
        endpoints = json.loads(args.expose_endpoints)  # type: Dict[str, Dict]
        for k, v in endpoints.items():
            expose_executor_endpoint(exec_endpoint=k, **v)

    if not args.default_swagger_ui:

        async def _render_custom_swagger_html(req: Request) -> HTMLResponse:
            import urllib.request

            swagger_url = 'https://api.jina.ai/swagger'
            req = urllib.request.Request(
                swagger_url, headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req) as f:
                return HTMLResponse(f.read().decode())

        app.add_route(docs_url, _render_custom_swagger_html, include_in_schema=False)

    async def _get_singleton_result(request_iterator) -> Dict:
        """
        Streams results from AsyncPrefetchCall as a dict

        :param request_iterator: request iterator, with length of 1
        :return: the first result from the request iterator
        """
        async for k in streamer.stream(request_iterator=request_iterator):
            return MessageToDict(
                k, including_default_value_fields=True, use_integers_for_enums=True
            )  # DO NOT customize other serialization here. Scheme is handled by Pydantic in `models.py`

    return app
