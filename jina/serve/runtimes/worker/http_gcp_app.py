from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Union, Any

from jina._docarray import docarray_v2
from jina.importer import ImportExtensions
from jina.types.request.data import DataRequest

if TYPE_CHECKING:
    from jina.logging.logger import JinaLogger

if docarray_v2:
    from docarray import BaseDoc, DocList


def get_fastapi_app(
    request_models_map: Dict,
    caller: Callable,
    logger: 'JinaLogger',
    cors: bool = False,
    **kwargs,
):
    """
    Get the app from FastAPI as the REST interface.

    :param request_models_map: Map describing the endpoints and its Pydantic models
    :param caller: Callable to be handled by the endpoints of the returned FastAPI app
    :param logger: Logger object
    :param cors: If set, a CORS middleware is added to FastAPI frontend to allow cross-origin access.
    :param kwargs: Extra kwargs to make it compatible with other methods
    :return: fastapi app
    """
    with ImportExtensions(required=True):
        import pydantic
        from fastapi import FastAPI, HTTPException, Request
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel, Field
        from pydantic.config import BaseConfig, inherit_config

    import os

    from jina.proto import jina_pb2
    from jina.serve.runtimes.gateway.models import _to_camel_case

    if not docarray_v2:
        logger.warning('Only docarray v2 is supported with Sagemaker. ')
        return

    class Header(BaseModel):
        request_id: Optional[str] = Field(
            description='Request ID', example=os.urandom(16).hex()
        )

        class Config(BaseConfig):
            alias_generator = _to_camel_case
            allow_population_by_field_name = True

    class InnerConfig(BaseConfig):
        alias_generator = _to_camel_case
        allow_population_by_field_name = True

    class VertexAIResponse(BaseModel):
        predictions: Any = Field(
            description='Prediction results',
        )

    app = FastAPI()

    if cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=True,
            allow_methods=['*'],
            allow_headers=['*'],
        )
        logger.warning('CORS is enabled. This service is accessible from any website!')

    def add_post_route(
        endpoint_path,
        input_model,
        output_model,
        input_doc_list_model=None,
    ):
        from docarray.base_doc.docarray_response import DocArrayResponse

        app_kwargs = dict(
            path=f'/{endpoint_path.strip("/")}',
            methods=['POST'],
            summary=f'Endpoint {endpoint_path}',
            response_model=Union[output_model, List[output_model]],
            response_class=DocArrayResponse,
        )

        def is_valid_csv(content: str) -> bool:
            import csv
            from io import StringIO

            try:
                f = StringIO(content)
                reader = csv.DictReader(f)
                for _ in reader:
                    pass

                return True
            except Exception:
                return False

        async def process(body) -> output_model:
            req = DataRequest()
            if body.header is not None:
                req.header.request_id = body.header.request_id

            if body.parameters is not None:
                req.parameters = body.parameters
            req.header.exec_endpoint = endpoint_path
            req.document_array_cls = DocList[input_doc_model]

            data = body.data
            if isinstance(data, list):
                req.data.docs = DocList[input_doc_list_model](data)
            else:
                req.data.docs = DocList[input_doc_list_model]([data])
                if body.header is None:
                    req.header.request_id = req.docs[0].id

            resp = await caller(req)
            status = resp.header.status

            if status.code == jina_pb2.StatusProto.ERROR:
                raise HTTPException(status_code=499, detail=status.description)
            else:
                return {"predictions": resp.docs}
                return output_model(predictions=resp.docs)

        @app.api_route(**app_kwargs)
        async def post(request: Request):
            content_type = request.headers.get('content-type')
            if content_type == 'application/json':
                json_body = await request.json()
                transformed_json_body = {"data": [{"text": instance} for instance in json_body["instances"]]}
                return await process(input_model(**transformed_json_body))

            elif content_type in ('text/csv', 'application/csv'):
                # TODO: fix here
                return await process(input_model(data=[]))
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f'Invalid content-type: {content_type}. '
                    f'Please use either application/json or text/csv.',
                )

    for endpoint, input_output_map in request_models_map.items():
        if endpoint != '_jina_dry_run_':
            input_doc_model = input_output_map['input']['model']
            parameters_model = input_output_map['parameters']['model'] or Optional[Dict]
            default_parameters = (
                ... if input_output_map['parameters']['model'] else None
            )

            _config = inherit_config(InnerConfig, BaseDoc.__config__)
            endpoint_input_model = pydantic.create_model(
                f'{endpoint.strip("/")}_input_model',
                data=(Union[List[input_doc_model], input_doc_model], ...),
                parameters=(parameters_model, default_parameters),
                header=(Optional[Header], None),
                __config__=_config,
            )

            add_post_route(
                endpoint,
                input_model=endpoint_input_model,
                output_model=VertexAIResponse,
                input_doc_list_model=input_doc_model,
            )

    from jina.serve.runtimes.gateway.health_model import JinaHealthModel

    # `/ping` route is required by AWS Sagemaker
    @app.get(
        path='/ping',
        summary='Get the health of Jina Executor service',
        response_model=JinaHealthModel,
    )
    async def _executor_health():
        """
        Get the health of this Gateway service.
        .. # noqa: DAR201

        """
        return {}

    return app
