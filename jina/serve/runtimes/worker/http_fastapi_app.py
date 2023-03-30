from typing import Dict, List, Optional, Callable

from jina.importer import ImportExtensions
from jina.types.request.data import DataRequest
from jina import DocumentArray


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
        from fastapi import FastAPI, Response
        import pydantic

    app = FastAPI()

    def add_route(endpoint_path, input_model, output_model):
        @app.api_route(
            path=f'/{endpoint_path.strip("/")}',
            methods=['POST'],
            summary=f'Endpoint {endpoint_path}',
            response_model=output_model
        )
        async def post(body: input_model, response: Response):
            req = DataRequest()
            req.data.docs = DocumentArray.from_pydantic_model(body.data)
            req.parameters = body.parameters
            req.header.exec_endpoint = endpoint_path
            resp = await caller(req)
            return output_model(data=resp.docs.to_dict(), parameters=resp.parameters)

    for endpoint, input_output_map in request_models_map.items():
        if endpoint != '_jina_dry_run_':
            input_doc_model = input_output_map['input']['model']
            output_doc_model = input_output_map['output']['model']

            endpoint_input_model = pydantic.create_model(
                f'{endpoint.strip("/")}_input_model',
                data=(List[input_doc_model], []),
                parameters=(Optional[Dict], None)
            )

            endpoint_output_model = pydantic.create_model(
                f'{endpoint.strip("/")}_output_model',
                data=(List[output_doc_model], []),
                parameters=(Optional[Dict], None)
            )

            add_route(endpoint, input_model=endpoint_input_model, output_model=endpoint_output_model)

    from jina.serve.runtimes.gateway.models import JinaHealthModel
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
