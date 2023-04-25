from typing import Dict, List, Optional, Callable

from jina.importer import ImportExtensions
from jina.types.request.data import DataRequest
from jina import DocumentArray
from jina._docarray import docarray_v2

if docarray_v2:
    from docarray import DocList


def get_fastapi_app(
        request_models_map: Dict,
        caller: Callable,
        **kwargs
):
    """
    Get the app from FastAPI as the REST interface.

    :param request_models_map: Map describing the endpoints and its Pydantic models
    :param caller: Callable to be handled by the endpoints of the returned FastAPI app
    :param kwargs: Extra kwargs to make it compatible with other methods
    :return: fastapi app
    """
    with ImportExtensions(required=True):
        from fastapi import FastAPI, Response, HTTPException
        import pydantic
    from jina.proto import jina_pb2

    app = FastAPI()

    def add_route(endpoint_path, input_model, output_model, input_doc_list_model=None, output_doc_list_model=None):
        app_kwargs = dict(path=f'/{endpoint_path.strip("/")}',
                          methods=['POST'],
                          summary=f'Endpoint {endpoint_path}',
                          response_model=output_model, )
        if docarray_v2:
            from docarray.base_doc.docarray_response import DocArrayResponse
            app_kwargs['response_class'] = DocArrayResponse

        @app.api_route(
            **app_kwargs
        )
        async def post(body: input_model, response: Response):
            req = DataRequest()
            if not docarray_v2:
                req.data.docs = DocumentArray.from_pydantic_model(body.data)
            else:
                req.data.docs = DocList[input_doc_list_model](body.data)
            req.parameters = body.parameters
            req.header.exec_endpoint = endpoint_path
            resp = await caller(req)
            status = resp.header.status
            if status.code == jina_pb2.StatusProto.ERROR:
                raise HTTPException(status_code=499, detail=status.description)
            else:
                if not docarray_v2:
                    docs_response = resp.docs.to_dict()
                else:
                    docs_response = resp.docs._data
                ret = output_model(data=docs_response, parameters=resp.parameters)
                return ret

    for endpoint, input_output_map in request_models_map.items():
        if endpoint != '_jina_dry_run_':
            input_doc_model = input_output_map['input']['model']
            output_doc_model = input_output_map['output']['model']

            endpoint_input_model = pydantic.create_model(
                f'{endpoint.strip("/")}_input_model',
                data=(List[input_doc_model], []),
                parameters=(Optional[Dict], None),
                __config__=input_doc_model.__config__
            )

            endpoint_output_model = pydantic.create_model(
                f'{endpoint.strip("/")}_output_model',
                data=(List[output_doc_model], []),
                parameters=(Optional[Dict], None),
                __config__=output_doc_model.__config__
            )

            add_route(endpoint,
                      input_model=endpoint_input_model,
                      output_model=endpoint_output_model,
                      input_doc_list_model=input_doc_model,
                      output_doc_list_model=output_doc_model)

    from jina.serve.runtimes.gateway.health_model import JinaHealthModel
    @app.get(
        path='/',
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
