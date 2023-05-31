import json
from typing import TYPE_CHECKING, Dict, List, Optional

from jina.clients.request import request_generator
from jina.enums import DataInputType
from jina.excepts import InternalNetworkError
from jina.helper import get_full_version
from jina.importer import ImportExtensions
from jina.logging.logger import JinaLogger

if TYPE_CHECKING:  # pragma: no cover
    from opentelemetry import trace

    from jina.serve.runtimes.gateway.streamer import GatewayStreamer


def get_fastapi_app(
        streamer: 'GatewayStreamer',
        title: str,
        description: str,
        no_debug_endpoints: bool,
        no_crud_endpoints: bool,
        expose_endpoints: Optional[str],
        expose_graphql_endpoint: bool,
        cors: bool,
        logger: 'JinaLogger',
        tracing: Optional[bool] = None,
        tracer_provider: Optional['trace.TracerProvider'] = None,
        **kwargs
):
    """
    Get the app from FastAPI as the REST interface.

    :param streamer: gateway streamer object
    :param title: The title of this HTTP server. It will be used in automatics docs such as Swagger UI.
    :param description: The description of this HTTP server. It will be used in automatics docs such as Swagger UI.
    :param no_debug_endpoints: If set, `/status` `/post` endpoints are removed from HTTP interface.
    :param no_crud_endpoints: If set, `/index`, `/search`, `/update`, `/delete` endpoints are removed from HTTP interface.

              Any executor that has `@requests(on=...)` bound with those values will receive data requests.
    :param expose_endpoints: A JSON string that represents a map from executor endpoints (`@requests(on=...)`) to HTTP endpoints.
    :param expose_graphql_endpoint: If set, /graphql endpoint is added to HTTP interface.
    :param cors: If set, a CORS middleware is added to FastAPI frontend to allow cross-origin access.
    :param logger: Jina logger.
    :param tracing: Enables tracing if set to True.
    :param tracer_provider: If tracing is enabled the tracer_provider will be used to instrument the code.
    :param kwargs: Extra kwargs to make it compatible with other methods
    :return: fastapi app
    """
    with ImportExtensions(required=True):
        from fastapi import FastAPI, Response, status
        from fastapi.middleware.cors import CORSMiddleware
        from jina.serve.runtimes.gateway.models import (
            JinaEndpointRequestModel,
            JinaRequestModel,
            JinaResponseModel,
        )
    from jina import __version__

    app = FastAPI(
        title=title or 'My Jina Service',
        description=description
                    or 'This is my awesome service. You can set `title` and `description` in your `Flow` or `Gateway` '
                       'to customize the title and description.',
        version=__version__,
    )

    if tracing:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)

    if cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )
        logger.warning('CORS is enabled. This service is accessible from any website!')

    @app.on_event('shutdown')
    async def _shutdown():
        await streamer.close()

    openapi_tags = []
    if not no_debug_endpoints:
        openapi_tags.append(
            {
                'name': 'Debug',
                'description': 'Debugging interface. In production, you should hide them by setting '
                               '`--no-debug-endpoints` in `Flow`/`Gateway`.',
            }
        )

        from jina._docarray import DocumentArray
        from jina.proto import jina_pb2
        from jina.serve.executors import __dry_run_endpoint__
        from jina.serve.runtimes.gateway.models import (
            PROTO_TO_PYDANTIC_MODELS
        )
        from jina.serve.runtimes.gateway.health_model import JinaInfoModel
        from jina.types.request.status import StatusMessage

        @app.get(
            path='/dry_run',
            summary='Get the readiness of Jina Flow service, sends an empty DocumentArray to the complete Flow to '
                    'validate connectivity',
            response_model=PROTO_TO_PYDANTIC_MODELS.StatusProto,
        )
        async def _flow_health():
            """
            Get the health of the complete Flow service.
            .. # noqa: DAR201

            """

            da = DocumentArray([])

            try:
                _ = await _get_singleton_result(
                    request_generator(
                        exec_endpoint=__dry_run_endpoint__,
                        data=da,
                        data_type=DataInputType.DOCUMENT,
                    )
                )
                status_message = StatusMessage()
                status_message.set_code(jina_pb2.StatusProto.SUCCESS)
                return status_message.to_dict()
            except Exception as ex:
                status_message = StatusMessage()
                status_message.set_exception(ex)
                return status_message.to_dict(use_integers_for_enums=True)

        @app.get(
            path='/status',
            summary='Get the status of Jina service',
            response_model=JinaInfoModel,
            tags=['Debug'],
        )
        async def _status():
            """
            Get the status of this Jina service.

            This is equivalent to running `jina -vf` from command line.

            .. # noqa: DAR201
            """
            version, env_info = get_full_version()
            for k, v in version.items():
                version[k] = str(v)
            for k, v in env_info.items():
                env_info[k] = str(v)
            return {'jina': version, 'envs': env_info}

        @app.post(
            path='/post',
            response_model=JinaResponseModel,
            # do not add response_model here, this debug endpoint should not restricts the response model
        )
        async def post(
                body: JinaEndpointRequestModel, response: Response
        ):  # 'response' is a FastAPI response, not a Jina response
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

            try:
                result = await _get_singleton_result(
                    request_generator(**req_generator_input)
                )
            except InternalNetworkError as err:
                import grpc

                if (
                        err.code() == grpc.StatusCode.UNAVAILABLE
                        or err.code() == grpc.StatusCode.NOT_FOUND
                ):
                    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
                elif err.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                    response.status_code = status.HTTP_504_GATEWAY_TIMEOUT
                else:
                    response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                result = bd  # send back the request
                result['header'] = _generate_exception_header(
                    err
                )  # attach exception details to response header
                logger.error(
                    f'Error while getting responses from deployments: {err.details()}'
                )
            return result

    def _generate_exception_header(error: InternalNetworkError):
        import traceback

        from jina.proto.serializer import DataRequest

        exception_dict = {
            'name': str(error.__class__),
            'stacks': [
                str(x) for x in traceback.extract_tb(error.og_exception.__traceback__)
            ],
            'executor': '',
        }
        status_dict = {
            'code': DataRequest().status.ERROR,
            'description': error.details() if error.details() else '',
            'exception': exception_dict,
        }
        header_dict = {'request_id': error.request_id, 'status': status_dict}
        return header_dict

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

        if kwargs['methods'] == ['POST']:
            @app.api_route(
                path=http_path or exec_endpoint, name=http_path or exec_endpoint, **kwargs
            )
            async def foo_post(body: JinaRequestModel, response: Response):
                from jina.enums import DataInputType
                bd = body.dict() if body else {'data': None}
                bd['exec_endpoint'] = exec_endpoint
                req_generator_input = bd
                req_generator_input['data_type'] = DataInputType.DICT
                if bd['data'] is not None and 'docs' in bd['data']:
                    req_generator_input['data'] = req_generator_input['data']['docs']

                try:
                    result = await _get_singleton_result(
                        request_generator(**req_generator_input)
                    )
                except InternalNetworkError as err:
                    import grpc

                    if (
                            err.code() == grpc.StatusCode.UNAVAILABLE
                            or err.code() == grpc.StatusCode.NOT_FOUND
                    ):
                        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
                    elif err.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                        response.status_code = status.HTTP_504_GATEWAY_TIMEOUT
                    else:
                        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                    result = bd  # send back the request
                    result['header'] = _generate_exception_header(
                        err
                    )  # attach exception details to response header
                    logger.error(
                        f'Error while getting responses from deployments: {err.details()}'
                    )
                return result
        else:
            @app.api_route(
                path=http_path or exec_endpoint, name=http_path or exec_endpoint, **kwargs
            )
            async def foo_no_post(body: JinaRequestModel):
                from jina.enums import DataInputType
                bd = body.dict() if body else {'data': None}
                bd['exec_endpoint'] = exec_endpoint
                req_generator_input = bd
                req_generator_input['data_type'] = DataInputType.DICT
                if bd['data'] is not None and 'docs' in bd['data']:
                    req_generator_input['data'] = req_generator_input['data']['docs']

                return await _get_singleton_result(
                    request_generator(**req_generator_input)
                )

    if not no_crud_endpoints:
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

    if expose_endpoints:
        endpoints = json.loads(expose_endpoints)  # type: Dict[str, Dict]
        for k, v in endpoints.items():
            expose_executor_endpoint(exec_endpoint=k, **v)

    if expose_graphql_endpoint:
        with ImportExtensions(required=True):
            from dataclasses import asdict

            import strawberry
            from strawberry.fastapi import GraphQLRouter

            from jina._docarray import DocumentArray, docarray_v2

            if not docarray_v2:
                from docarray.document.strawberry_type import (
                    JSONScalar,
                    StrawberryDocument,
                    StrawberryDocumentInput,
                )
            else:
                raise NotImplementedError('GraphQL is not yet supported for DocArrayV2')

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
                try:
                    response = await _get_singleton_result(
                        request_generator(**req_generator_input)
                    )
                except InternalNetworkError as err:
                    logger.error(
                        f'Error while getting responses from deployments: {err.details()}'
                    )
                    raise err  # will be handled by Strawberry
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
        from jina._docarray import docarray_v2

        async for result in streamer.rpc_stream(request_iterator=request_iterator):
            if not docarray_v2:
                for i in range(len(result.data._content.docs.docs)):
                    if result.data._content.docs.docs[i].HasField('embedding'):
                        result.data._content.docs.docs[i].embedding.cls_name = 'numpy'
                    if result.data._content.docs.docs[i].HasField('tensor'):
                        result.data._content.docs.docs[i].tensor.cls_name = 'numpy'
            result_dict = result.to_dict()
            return result_dict

    return app
