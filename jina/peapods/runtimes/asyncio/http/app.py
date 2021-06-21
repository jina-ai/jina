import argparse
import json
from typing import Dict

from google.protobuf.json_format import MessageToJson

from ..grpc.async_call import AsyncPrefetchCall
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
        from fastapi.middleware.cors import CORSMiddleware
        from starlette.responses import StreamingResponse
        from .models import (
            JinaStatusModel,
            JinaRequestModel,
        )

    app = FastAPI(
        title=args.title or 'My Jina Service',
        description=args.description
        or 'This is my awesome service. You can set `title` and `description` in your `Flow` or `Gateway` '
        'to customize this text.',
        version=__version__,
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

    zmqlet = AsyncZmqlet(args, logger)
    servicer = AsyncPrefetchCall(args, zmqlet)

    @app.on_event('shutdown')
    def _shutdown():
        zmqlet.close()

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
            response_model=JinaRequestModel,
            tags=['Debug'],
        )
        async def post(body: JinaRequestModel):
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
            return StreamingResponse(
                result_in_stream(request_generator(**bd)), media_type='application/json'
            )

    def expose_executor_endpoint(exec_endpoint, http_path=None, **kwargs):
        """Exposing an executor endpoint to http endpoint
        :param exec_endpoint: the executor endpoint
        :param http_path: the http endpoint
        :param kwargs: kwargs accepted by FastAPI
        """

        # set some default kwargs for richer semantics
        # group flow exposed endpoints into `customized` group
        kwargs['tags'] = kwargs.get('tags', ['Customized'])
        # add fullrequest as response model
        kwargs['response_model'] = kwargs.get('response_model', JinaRequestModel)

        @app.api_route(
            path=http_path or exec_endpoint, name=http_path or exec_endpoint, **kwargs
        )
        async def foo(body: JinaRequestModel):
            bd = body.dict() if body else {'data': None}
            bd['exec_endpoint'] = exec_endpoint
            return StreamingResponse(
                result_in_stream(request_generator(**bd)), media_type='application/json'
            )

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
                'summary'
            ] = f'Post data requests to the Flow. Executors with `@requests(on="{k}")` will respond.'
            expose_executor_endpoint(exec_endpoint=k, **v)

    if openapi_tags:
        app.openapi_tags = openapi_tags

    if args.expose_endpoints:
        endpoints = json.loads(args.expose_endpoints)  # type: Dict[str, Dict]
        for k, v in endpoints.items():
            expose_executor_endpoint(exec_endpoint=k, **v)

    async def result_in_stream(req_iter):
        """
        Streams results from AsyncPrefetchCall as json

        :param req_iter: request iterator
        :yield: result
        """
        async for k in servicer.Call(request_iterator=req_iter, context=None):
            yield MessageToJson(
                k,
                including_default_value_fields=args.including_default_value_fields,
                preserving_proto_field_name=True,
                sort_keys=args.sort_keys,
                use_integers_for_enums=args.use_integers_for_enums,
                float_precision=args.float_precision,
            )

    return app
