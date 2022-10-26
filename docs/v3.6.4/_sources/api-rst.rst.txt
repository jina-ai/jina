======================
:fab:`python` Python API
======================

This section includes the API documentation from the `jina` codebase, as extracted from the `docstrings <https://peps.python.org/pep-0257/>`_ in the code.

For further details, please refer to the full :ref:`user guide <executor-cookbook>`.


:mod:`jina.orchestrate.flow` - Flow
--------------------

.. currentmodule:: jina.orchestrate.flow

.. autosummary::
   :nosignatures:
   :template: class.rst

   base.Flow
   asyncio.AsyncFlow


:mod:`jina.serve.executors` - Executor
--------------------

.. currentmodule:: jina.serve.executors

.. autosummary::
   :nosignatures:
   :template: class.rst

   Executor
   BaseExecutor
   decorators.requests
   decorators.monitor


:mod:`jina.clients` - Clients
--------------------

.. currentmodule:: jina.clients

.. autosummary::
   :nosignatures:
   :template: class.rst

   Client
   grpc.GRPCClient
   grpc.AsyncGRPCClient
   http.HTTPClient
   http.AsyncHTTPClient
   websocket.WebSocketClient
   websocket.AsyncWebSocketClient



:mod:`jina.serve.runtimes` - Internals
--------------------

.. currentmodule:: jina.serve.runtimes

.. autosummary::
   :nosignatures:
   :template: class.rst

   asyncio.AsyncNewLoopRuntime
   gateway.GatewayRuntime
   gateway.grpc.GRPCGatewayRuntime
   gateway.http.HTTPGatewayRuntime
   gateway.websocket.WebSocketGatewayRuntime
   worker.WorkerRuntime
   head.HeadRuntime
