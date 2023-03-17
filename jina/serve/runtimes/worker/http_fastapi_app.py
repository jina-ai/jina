from typing import Dict

from jina.importer import ImportExtensions


def get_fastapi_app(
        request_models_map: Dict,
        **kwargs
):
    with ImportExtensions(required=True):
        from fastapi import FastAPI, APIRouter, Response

        from jina._docarray import docarray_v2, DocumentArray
    if not docarray_v2:
        from docarray.document.pydantic_model import PydanticDocumentArray

    app = FastAPI()

    def create_router(endpoint_path, input_model, output_model):
        router = APIRouter()

        @router.post(f'/{endpoint_path.strip("/")}', response_model=output_model, summary=f'Endpoint {endpoint_path}')
        async def post(body: input_model, response: Response):
            return DocumentArray.empty(2).to_dict()

        return router

    for endpoint, input_output_map in request_models_map.items():
        if endpoint != '_jina_dry_run_':
            input_model = input_output_map['input']
            input_model = PydanticDocumentArray
            output_model = input_output_map['output']
            output_model = PydanticDocumentArray
            router = create_router(endpoint, input_model=input_model, output_model=output_model)
            app.include_router(router)

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
