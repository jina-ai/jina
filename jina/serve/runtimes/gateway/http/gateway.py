from typing import Optional

from jina.serve.runtimes.gateway.http.app import get_fastapi_app
from jina.serve.runtimes.gateway.http.fastapi import FastAPIBaseGateway


class HTTPGateway(FastAPIBaseGateway):
    """HTTP Gateway implementation"""

    def __init__(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        no_debug_endpoints: Optional[bool] = False,
        no_crud_endpoints: Optional[bool] = False,
        expose_endpoints: Optional[str] = None,
        expose_graphql_endpoint: Optional[bool] = False,
        cors: Optional[bool] = False,
        **kwargs
    ):
        """Initialize the gateway
            Get the app from FastAPI as the REST interface.
        :param title: The title of this HTTP server. It will be used in automatics docs such as Swagger UI.
        :param description: The description of this HTTP server. It will be used in automatics docs such as Swagger UI.
        :param no_debug_endpoints: If set, `/status` `/post` endpoints are removed from HTTP interface.
        :param no_crud_endpoints: If set, `/index`, `/search`, `/update`, `/delete` endpoints are removed from HTTP interface.

                  Any executor that has `@requests(on=...)` bound with those values will receive data requests.
        :param expose_endpoints: A JSON string that represents a map from executor endpoints (`@requests(on=...)`) to HTTP endpoints.
        :param expose_graphql_endpoint: If set, /graphql endpoint is added to HTTP interface.
        :param cors: If set, a CORS middleware is added to FastAPI frontend to allow cross-origin access.
        :param kwargs: keyword args
        """
        super().__init__(**kwargs)
        self.title = title
        self.description = description
        self.no_debug_endpoints = no_debug_endpoints
        self.no_crud_endpoints = no_crud_endpoints
        self.expose_endpoints = expose_endpoints
        self.expose_graphql_endpoint = expose_graphql_endpoint
        self.cors = cors

    @property
    def app(self):
        """
        FastAPI app needed to define an HTTP Jina Gateway

        :return: FastAPI app
        """
        from jina.helper import extend_rest_interface

        return extend_rest_interface(
            get_fastapi_app(
                streamer=self.streamer,
                title=self.title,
                description=self.description,
                no_debug_endpoints=self.no_debug_endpoints,
                no_crud_endpoints=self.no_crud_endpoints,
                expose_endpoints=self.expose_endpoints,
                expose_graphql_endpoint=self.expose_graphql_endpoint,
                cors=self.cors,
                logger=self.logger,
                tracing=self.tracing,
                tracer_provider=self.tracer_provider,
            )
        )
