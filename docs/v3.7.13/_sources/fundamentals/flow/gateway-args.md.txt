| Name | Description | Type | Default |
|----|----|----|----|
| `name` | The name of this object.<br><br>    This will be used in the following places:<br>    - how you refer to this object in Python/YAML/CLI<br>    - visualization<br>    - log message header<br>    - ...<br><br>    When not given, then the default naming strategy will apply. | `string` | `gateway` |
| `workspace` | The working directory for any IO operations in this object. If not set, then derive from its parent `workspace`. | `string` | `None` |
| `log_config` | The YAML config of the logger used in this object. | `string` | `default` |
| `quiet` | If set, then no log will be emitted from this object. | `boolean` | `False` |
| `quiet_error` | If set, then exception stack information will not be added to the log | `boolean` | `False` |
| `timeout_ctrl` | The timeout in milliseconds of the control request, -1 for waiting forever | `number` | `60` |
| `polling` | The polling strategy of the Deployment and its endpoints (when `shards>1`).<br>    Can be defined for all endpoints of a Deployment or by endpoint.<br>    Define per Deployment:<br>    - ANY: only one (whoever is idle) Pod polls the message<br>    - ALL: all Pods poll the message (like a broadcast)<br>    Define per Endpoint:<br>    JSON dict, {endpoint: PollingType}<br>    {'/custom': 'ALL', '/search': 'ANY', '*': 'ANY'} | `string` | `ANY` |
| `uses` | The config of the executor, it could be one of the followings:<br>        * an Executor YAML file (.yml, .yaml, .jaml)<br>        * a Jina Hub Executor (must start with `jinahub://` or `jinahub+docker://`)<br>        * a docker image (must start with `docker://`)<br>        * the string literal of a YAML config (must start with `!` or `jtype: `)<br>        * the string literal of a JSON config<br><br>        When use it under Python, one can use the following values additionally:<br>        - a Python dict that represents the config<br>        - a text file stream has `.read()` interface | `string` | `BaseExecutor` |
| `uses_with` | Dictionary of keyword arguments that will override the `with` configuration in `uses` | `object` | `None` |
| `uses_metas` | Dictionary of keyword arguments that will override the `metas` configuration in `uses` | `object` | `None` |
| `uses_requests` | Dictionary of keyword arguments that will override the `requests` configuration in `uses` | `object` | `None` |
| `py_modules` | The customized python modules need to be imported before loading the executor<br><br>Note that the recommended way is to only import a single module - a simple python file, if your<br>executor can be defined in a single file, or an ``__init__.py`` file if you have multiple files,<br>which should be structured as a python package. For more details, please see the<br>`Executor cookbook <https://docs.jina.ai/fundamentals/executor/executor-files/>`__ | `array` | `None` |
| `port` | The port for input data to bind to, default is a random port between [49152, 65535] | `number` | `random in [49152, 65535]` |
| `host_in` | The host address for binding to, by default it is 0.0.0.0 | `string` | `0.0.0.0` |
| `native` | If set, only native Executors is allowed, and the Executor is always run inside WorkerRuntime. | `boolean` | `False` |
| `output_array_type` | The type of array `tensor` and `embedding` will be serialized to.<br><br>Supports the same types as `docarray.to_protobuf(.., ndarray_type=...)`, which can be found <br>`here <https://docarray.jina.ai/fundamentals/document/serialization/#from-to-protobuf>`.<br>Defaults to retaining whatever type is returned by the Executor. | `string` | `None` |
| `prefetch` | Number of requests fetched from the client before feeding into the first Executor. <br>    <br>    Used to control the speed of data input into a Flow. 0 disables prefetch (1000 requests is the default) | `number` | `1000` |
| `title` | The title of this HTTP server. It will be used in automatics docs such as Swagger UI. | `string` | `None` |
| `description` | The description of this HTTP server. It will be used in automatics docs such as Swagger UI. | `string` | `None` |
| `cors` | If set, a CORS middleware is added to FastAPI frontend to allow cross-origin access. | `boolean` | `False` |
| `no_debug_endpoints` | If set, `/status` `/post` endpoints are removed from HTTP interface. | `boolean` | `False` |
| `no_crud_endpoints` | If set, `/index`, `/search`, `/update`, `/delete` endpoints are removed from HTTP interface.<br><br>        Any executor that has `@requests(on=...)` bind with those values will receive data requests. | `boolean` | `False` |
| `expose_endpoints` | A JSON string that represents a map from executor endpoints (`@requests(on=...)`) to HTTP endpoints. | `string` | `None` |
| `uvicorn_kwargs` | Dictionary of kwargs arguments that will be passed to Uvicorn server when starting the server<br><br>More details can be found in Uvicorn docs: https://www.uvicorn.org/settings/ | `object` | `None` |
| `grpc_server_kwargs` | Dictionary of kwargs arguments that will be passed to the grpc server when starting the server # todo update | `object` | `None` |
| `ssl_certfile` | the path to the certificate file | `string` | `None` |
| `ssl_keyfile` | the path to the key file | `string` | `None` |
| `expose_graphql_endpoint` | If set, /graphql endpoint is added to HTTP interface. | `boolean` | `False` |
| `protocol` | Communication protocol between server and client. | `string` | `GRPC` |
| `host` | The host address of the runtime, by default it is 0.0.0.0. | `string` | `0.0.0.0` |
| `proxy` | If set, respect the http_proxy and https_proxy environment variables. otherwise, it will unset these proxy variables before start. gRPC seems to prefer no proxy | `boolean` | `False` |
| `graph_description` | Routing graph for the gateway | `string` | `{}` |
| `graph_conditions` | Dictionary stating which filtering conditions each Executor in the graph requires to receive Documents. | `string` | `{}` |
| `deployments_addresses` | dictionary JSON with the input addresses of each Deployment | `string` | `{}` |
| `deployments_disable_reduce` | list JSON disabling the built-in merging mechanism for each Deployment listed | `string` | `[]` |
| `compression` | The compression mechanism used when sending requests from the Head to the WorkerRuntimes. For more details, check https://grpc.github.io/grpc/python/grpc.html#compression. | `string` | `None` |
| `timeout_send` | The timeout in milliseconds used when sending data requests to Executors, -1 means no timeout, disabled by default | `number` | `None` |
| `runtime_cls` | The runtime class to run inside the Pod | `string` | `GRPCGatewayRuntime` |
| `timeout_ready` | The timeout in milliseconds of a Pod waits for the runtime to be ready, -1 for waiting forever | `number` | `600000` |
| `env` | The map of environment variables that are available inside runtime | `object` | `None` |
| `shards` | The number of shards in the deployment running at the same time. For more details check https://docs.jina.ai/fundamentals/flow/create-flow/#complex-flow-topologies | `number` | `1` |
| `replicas` | The number of replicas in the deployment | `number` | `1` |
| `monitoring` | If set, spawn an http server with a prometheus endpoint to expose metrics | `boolean` | `False` |
| `port_monitoring` | The port on which the prometheus server is exposed, default is a random port between [49152, 65535] | `number` | `random in [49152, 65535]` |
| `retries` | Number of retries per gRPC call. If <0 it defaults to max(3, num_replicas) | `number` | `-1` |
| `floating` | If set, the current Pod/Deployment can not be further chained, and the next `.add()` will chain after the last Pod/Deployment not this current one. | `boolean` | `False` |