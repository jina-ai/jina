from typing import Dict

from jina.importer import ImportExtensions


def get_fastapi_app(
        request_models_map: Dict,
        **kwargs
):
    with ImportExtensions(required=True):
        from fastapi import FastAPI, APIRouter, Response
        import pydantic

        from jina._docarray import DocumentArray

    app = FastAPI()

    def create_router(endpoint_path, input_model, output_model):
        router = APIRouter()

        @router.post(f'/{endpoint_path.strip("/")}', response_model=output_model, summary=f'Endpoint {endpoint_path}')
        async def post(body: input_model, response: Response):
            return DocumentArray.empty(2).to_dict()

        return router

    for endpoint, input_output_map in request_models_map.items():
        if endpoint != '_jina_dry_run_':
            input_model_name = input_output_map['input']['name']
            input_model_schema = input_output_map['input']['schema']
            request_model = pydantic.create_model(f'{endpoint}_request_{input_model_name}', **input_model_schema)
            output_model_name = input_output_map['input']['name']
            output_model_schema = input_output_map['input']['schema']
            response_model = pydantic.create_model(f'{endpoint}_response_{output_model_name}', **output_model_schema)
            router = create_router(endpoint, input_model=request_model, output_model=response_model)
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
