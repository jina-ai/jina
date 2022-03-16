import argparse
import json
import warnings
from typing import TYPE_CHECKING, Dict, List, Optional

from jina import __version__
from jina.clients.request import request_generator
from jina.enums import DataInputType
from jina.helper import (
    GRAPHQL_MIN_DOCARRAY_VERSION,
    docarray_graphql_compatible,
    get_full_version,
)
from jina.importer import ImportExtensions
from jina.logging.logger import JinaLogger
from jina.logging.profile import used_memory_readable

if TYPE_CHECKING:
    from jina.serve.networking import GrpcConnectionPool
    from jina.serve.runtimes.gateway.graph.topology_graph import TopologyGraph


def get_fastapi_app(
    args: 'argparse.Namespace',
    topology_graph: 'TopologyGraph',
    connection_pool: 'GrpcConnectionPool',
    logger: 'JinaLogger',
):
    """
    Get the app from FastAPI as the REST interface.

    :param args: passed arguments.
    :param topology_graph: topology graph that manages the logic of sending to the proper executors.
    :param connection_pool: Connection Pool to handle multiple replicas and sending to different of them
    :param logger: Jina logger.
    :return: fastapi app
    """
    with ImportExtensions(required=True):
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from fastapi.responses import HTMLResponse
        from starlette.requests import Request

        from jina.serve.runtimes.gateway.http.models import (
            JinaEndpointRequestModel,
            JinaRequestModel,
            JinaResponseModel,
            JinaStatusModel,
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

    if args.expose_graphql_endpoint and not docarray_graphql_compatible():
        args.expose_graphql_endpoint = False
        warnings.warn(
            'DocArray version is incompatible with GraphQL features.'
            'Setting expose_graphql_endpoint=False.'
            f'To use GraphQL features, install docarray>={GRAPHQL_MIN_DOCARRAY_VERSION}'
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

    from jina.serve.runtimes.gateway.request_handling import (
        handle_request,
        handle_result,
    )
    from jina.serve.stream import RequestStreamer

    streamer = RequestStreamer(
        args=args,
        request_handler=handle_request(
            graph=topology_graph, connection_pool=connection_pool
        ),
        result_handler=handle_result,
    )
    streamer.Call = streamer.stream

    @app.on_event('shutdown')
    async def _shutdown():
        await connection_pool.close()

    openapi_tags = []
    if not args.no_debug_endpoints:
        openapi_tags.append(
            {
                'name': 'Debug',
                'description': 'Debugging interface. In production, you should hide them by setting '
                '`--no-debug-endpoints` in `Flow`/`Gateway`.',
            }
        )

        from jina.serve.runtimes.gateway.http.models import JinaHealthModel

        @app.get(
            path='/',
            summary='Get the health of Jina service',
            response_model=JinaHealthModel,
        )
        async def _health():
            """
            Get the health of this Jina service.
            .. # noqa: DAR201

            """
            return {}

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
            response_model=JinaResponseModel,
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
            from jina.enums import DataInputType

            bd = body.dict()  # type: Dict
            req_generator_input = bd
            req_generator_input['data_type'] = DataInputType.DICT
            if bd['data'] is not None and 'docs' in bd['data']:
                req_generator_input['data'] = req_generator_input['data']['docs']

            result = await _get_singleton_result(
                request_generator(**req_generator_input)
            )
            return result

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
            from jina.enums import DataInputType

            bd = body.dict() if body else {'data': None}
            bd['exec_endpoint'] = exec_endpoint
            req_generator_input = bd
            req_generator_input['data_type'] = DataInputType.DICT
            if bd['data'] is not None and 'docs' in bd['data']:
                req_generator_input['data'] = req_generator_input['data']['docs']

            result = await _get_singleton_result(
                request_generator(**req_generator_input)
            )
            return result

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

    if args.expose_graphql_endpoint:
        with ImportExtensions(required=True):
            from dataclasses import asdict

            import strawberry
            from docarray.document.strawberry_type import (
                JSONScalar,
                StrawberryDocument,
                StrawberryDocumentInput,
            )
            from strawberry.fastapi import GraphQLRouter

            from docarray import DocumentArray

            async def get_docs_from_endpoint(
                data, target_executor, parameters, exec_endpoint
            ):
                req_generator_input = {
                    'data': [asdict(d) for d in data],
                    'target_executor': target_executor,
                    'parameters': parameters,
                    'exec_endpoint': exec_endpoint,
                    'data_type': DataInputType.DICT,
                }

                if (
                    req_generator_input['data'] is not None
                    and 'docs' in req_generator_input['data']
                ):
                    req_generator_input['data'] = req_generator_input['data']['docs']

                response = await _get_singleton_result(
                    request_generator(**req_generator_input)
                )
                return DocumentArray.from_dict(response['data']).to_strawberry_type()

            @strawberry.type
            class Mutation:
                @strawberry.mutation
                async def docs(
                    self,
                    data: Optional[List[StrawberryDocumentInput]] = None,
                    target_executor: Optional[str] = None,
                    parameters: Optional[JSONScalar] = None,
                    exec_endpoint: str = '/search',
                ) -> List[StrawberryDocument]:
                    return await get_docs_from_endpoint(
                        data, target_executor, parameters, exec_endpoint
                    )

            @strawberry.type
            class Query:
                @strawberry.field
                async def docs(
                    self,
                    data: Optional[List[StrawberryDocumentInput]] = None,
                    target_executor: Optional[str] = None,
                    parameters: Optional[JSONScalar] = None,
                    exec_endpoint: str = '/search',
                ) -> List[StrawberryDocument]:
                    return await get_docs_from_endpoint(
                        data, target_executor, parameters, exec_endpoint
                    )

            schema = strawberry.Schema(query=Query, mutation=Mutation)
            app.include_router(GraphQLRouter(schema), prefix='/graphql')

    async def _get_singleton_result(request_iterator) -> Dict:
        """
        Streams results from AsyncPrefetchCall as a dict

        :param request_iterator: request iterator, with length of 1
        :return: the first result from the request iterator
        """
        async for k in streamer.stream(request_iterator=request_iterator):
            request_dict = k.to_dict()
            return request_dict

    return app
