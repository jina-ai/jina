import asyncio

from jina.serve.runtimes.gateway import GatewayRuntime
from jina.serve.runtimes.gateway.websocket.app import get_fastapi_app

__all__ = ['WebSocketGatewayRuntime']

from jina.serve.runtimes.gateway.websocket.gateway import WebSocketGateway
