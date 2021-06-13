import json

import requests
from pydantic import BaseModel
from starlette.responses import StreamingResponse

import jina.helper
from jina import Flow
from jina.peapods.runtimes.asyncio.rest.models import JinaRequestModel


def test_extend_fastapi():
    def extend_rest_function(app):
        @app.get('/hello', tags=['My Extended APIs'])
        async def foo():
            return {'msg': 'hello world'}

        return app

    jina.helper.extend_rest_interface = extend_rest_function
    f = Flow(restful=True)

    with f:
        response = requests.get(f'http://localhost:{f.port_expose}/hello')
        assert response.status_code == 200
        assert response.json() == {'msg': 'hello world'}


def test_extend_fastapi_send_documents():
    class CustomRequestModel(BaseModel):
        custom_request_attribute: str

    class CustomResponseModel(BaseModel):
        custom_response_attribute: str

    def map_request(request):
        return JinaRequestModel(data=[request.custom_request_attribute])

    async def map_response(search_resp):
        async for x in search_resp:
            yield json.dumps(
                CustomResponseModel(
                    custom_response_attribute=x.data.docs[0].text
                ).dict()
            )

    def extend_rest_function(app, send_request):
        @app.post(
            path='/hello_flow',
            response_model=CustomResponseModel,
        )
        async def search_docs(body: CustomRequestModel):
            search_req = map_request(body)
            search_resp = send_request(search_req, 'hello_flow')
            final_response = map_response(search_resp)
            return StreamingResponse(final_response, media_type='application/json')

        return app

    jina.helper.extend_rest_interface = extend_rest_function
    f = Flow(restful=True)

    with f:
        response = requests.post(
            f'http://localhost:{f.port_expose}/hello_flow',
            json={'custom_request_attribute': 'example_text'},
        )
        assert response.status_code == 200
        assert response.json() == {'custom_response_attribute': 'example_text'}
