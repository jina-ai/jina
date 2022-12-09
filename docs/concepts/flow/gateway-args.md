| Name | Description | Type | Default |
|----|----|----|----|
| `name` | The name of this object.<br><br>    This will be used in the following places:<br>    - how you refer to this object in Python/YAML/CLI<br>    - visualization<br>    - log message header<br>    - ...<br><br>    When not given, then the default naming strategy will apply. | `string` | `gateway` |
| `workspace` | The working directory for any IO operations in this object. If not set, then derive from its parent `workspace`. | `string` | `None` |
| `log_config` | The YAML config of the logger used in this object. | `string` | `default` |
| `quiet` | If set, then no log will be emitted from this object. | `boolean` | `False` |
| `quiet_error` | If set, then exception stack information will not be added to the log | `boolean` | `False` |
| `timeout_ctrl` | The timeout in milliseconds of the control request, -1 for waiting forever | `number` | `60` |
| `entrypoint` | The entrypoint command overrides the ENTRYPOINT in Docker image. when not set then the Docker image ENTRYPOINT takes effective. | `string` | `None` |
| `docker_kwargs` | Dictionary of kwargs arguments that will be passed to Docker SDK when starting the docker '<br>container. <br><br>More details can be found in the Docker SDK docs:  https://docker-py.readthedocs.io/en/stable/ | `object` | `None` |
| `prefetch` | Number of requests fetched from the client before feeding into the first Executor. <br>    <br>    Used to control the speed of data input into a Flow. 0 disables prefetch (1000 requests is the default) | `number` | `1000` |
| `title` | The title of this HTTP server. It will be used in automatics docs such as Swagger UI. | `string` | `None` |
| `description` | The description of this HTTP server. It will be used in automatics docs such as Swagger UI. | `string` | `None` |
| `cors` | If set, a CORS middleware is added to FastAPI frontend to allow cross-origin access. | `boolean` | `False` |
| `no_debug_endpoints` | If set, `/status` `/post` endpoints are removed from HTTP interface. | `boolean` | `False` |
| `no_crud_endpoints` | If set, `/index`, `/search`, `/update`, `/delete` endpoints are removed from HTTP interface.<br><br>        Any executor that has `@requests(on=...)` bound with those values will receive data requests. | `boolean` | `False` |
| `expose_endpoints` | A JSON string that represents a map from executor endpoints (`@requests(on=...)`) to HTTP endpoints. | `string` | `None` |
| `uvicorn_kwargs` | Dictionary of kwargs arguments that will be passed to Uvicorn server when starting the server<br><br>More details can be found in Uvicorn docs: https://www.uvicorn.org/settings/ | `object` | `None` |
| `ssl_certfile` | the path to the certificate file | `string` | `None` |
| `ssl_keyfile` | the path to the key file | `string` | `None` |
| `expose_graphql_endpoint` | If set, /graphql endpoint is added to HTTP interface. | `boolean` | `False` |
| `protocol` | Communication protocol of the server exposed by the Gateway. This can be a single value or a list of protocols, depending on your chosen Gateway. Choose the convenient protocols from: ['GRPC', 'HTTP', 'WEBSOCKET']. | `array` | `[<GatewayProtocolType.GRPC: 0>]` |
| `host` | The host address of the runtime, by default it is 0.0.0.0. In the case of an external Executor (`--external` or `external=True`) this can be a list of hosts, separated by commas. Then, every resulting address will be considered as one replica of the Executor. | `string` | `0.0.0.0` |
| `proxy` | If set, respect the http_proxy and https_proxy environment variables. otherwise, it will unset these proxy variables before start. gRPC seems to prefer no proxy | `boolean` | `False` |
| `uses` | The config of the gateway, it could be one of the followings:<br>        * the string literal of an Gateway class name<br>        * a Gateway YAML file (.yml, .yaml, .jaml)<br>        * a docker image (must start with `docker://`)<br>        * the string literal of a YAML config (must start with `!` or `jtype: `)<br>        * the string literal of a JSON config<br><br>        When use it under Python, one can use the following values additionally:<br>        - a Python dict that represents the config<br>        - a text file stream has `.read()` interface | `string` | `None` |
| `uses_with` | Dictionary of keyword arguments that will override the `with` configuration in `uses` | `object` | `None` |
| `py_modules` | The customized python modules need to be imported before loading the gateway<br><br>Note that the recommended way is to only import a single module - a simple python file, if your<br>gateway can be defined in a single file, or an ``__init__.py`` file if you have multiple files,<br>which should be structured as a python package. | `array` | `None` |
| `grpc_server_options` | Dictionary of kwargs arguments that will be passed to the grpc server as options when starting the server, example : {'grpc.max_send_message_length': -1} | `object` | `None` |
| `graph_description` | Routing graph for the gateway | `string` | `{}` |
| `graph_conditions` | Dictionary stating which filtering conditions each Executor in the graph requires to receive Documents. | `string` | `{}` |
| `deployments_addresses` | JSON dictionary with the input addresses of each Deployment | `string` | `{}` |
| `deployments_metadata` | JSON dictionary with the request metadata for each Deployment | `string` | `{}` |
| `deployments_no_reduce` | list JSON disabling the built-in merging mechanism for each Deployment listed | `string` | `[]` |
| `compression` | The compression mechanism used when sending requests from the Head to the WorkerRuntimes. For more details, check https://grpc.github.io/grpc/python/grpc.html#compression. | `string` | `None` |
| `timeout_send` | The timeout in milliseconds used when sending data requests to Executors, -1 means no timeout, disabled by default | `number` | `None` |
| `runtime_cls` | The runtime class to run inside the Pod | `string` | `GatewayRuntime` |
| `timeout_ready` | The timeout in milliseconds of a Pod waits for the runtime to be ready, -1 for waiting forever | `number` | `600000` |
| `env` | The map of environment variables that are available inside runtime | `object` | `None` |
| `floating` | If set, the current Pod/Deployment can not be further chained, and the next `.add()` will chain after the last Pod/Deployment not this current one. | `boolean` | `False` |
| `restart` | If set, the Gateway will restart while serving if the YAML configuration source is changed. | `boolean` | `False` |
| `port` | The port for input data to bind the gateway server to, by default, random ports between range [49152, 65535] will be assigned. The port argument can be either 1 single value in case only 1 protocol is used or multiple values when many protocols are used. | `null` | `random in [49152, 65535]` |
| `monitoring` | If set, spawn an http server with a prometheus endpoint to expose metrics | `boolean` | `False` |
| `port_monitoring` | The port on which the prometheus server is exposed, default is a random port between [49152, 65535] | `string` | `random in [49152, 65535]` |
| `retries` | Number of retries per gRPC call. If <0 it defaults to max(3, num_replicas) | `number` | `-1` |
| `tracing` | If set, the sdk implementation of the OpenTelemetry tracer will be available and will be enabled for automatic tracing of requests and customer span creation. Otherwise a no-op implementation will be provided. | `boolean` | `False` |
| `traces_exporter_host` | If tracing is enabled, this hostname will be used to configure the trace exporter agent. | `string` | `None` |
| `traces_exporter_port` | If tracing is enabled, this port will be used to configure the trace exporter agent. | `number` | `None` |
| `metrics` | If set, the sdk implementation of the OpenTelemetry metrics will be available for default monitoring and custom measurements. Otherwise a no-op implementation will be provided. | `boolean` | `False` |
| `metrics_exporter_host` | If tracing is enabled, this hostname will be used to configure the metrics exporter agent. | `string` | `None` |
| `metrics_exporter_port` | If tracing is enabled, this port will be used to configure the metrics exporter agent. | `number` | `None` |