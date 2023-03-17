from typing import Dict

from jina.importer import ImportExtensions


def get_fastapi_app(
    request_models_map: Dict,
    **kwargs
):
    # TODO: Add code that from the Executor build a FastAPI app that maps the `request` and its Input and Output
    #  Models to `app.post` methods
    with ImportExtensions(required=True):
        from fastapi import FastAPI

    app = FastAPI(
    )

    return app
