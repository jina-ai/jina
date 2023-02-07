| Name | Description | Type | Default |
|----|----|----|----|
| `name` | The name of this object.<br><br>    This will be used in the following places:<br>    - how you refer to this object in Python/YAML/CLI<br>    - visualization<br>    - log message header<br>    - ...<br><br>    When not given, then the default naming strategy will apply. | `string` | `None` |
| `workspace` | The working directory for any IO operations in this object. If not set, then derive from its parent `workspace`. | `string` | `None` |
| `log_config` | The config name or the absolute path to the YAML config file of the logger used in this object. | `string` | `default` |
| `quiet` | If set, then no log will be emitted from this object. | `boolean` | `False` |
| `quiet_error` | If set, then exception stack information will not be added to the log | `boolean` | `False` |
| `timeout_ctrl` | The timeout in milliseconds of the control request, -1 for waiting forever | `number` | `60` |
| `native` | If set, only native Executors is allowed, and the Executor is always run inside WorkerRuntime. | `boolean` | `False` |
| `uses` | The config of the executor, it could be one of the followings:<br>        * the string literal of an Executor class name<br>        * an Executor YAML file (.yml, .yaml, .jaml)<br>        * a Jina Hub Executor (must start with `jinahub://` or `jinahub+docker://`)<br>        * a docker image (must start with `docker://`)<br>        * the string literal of a YAML config (must start with `!` or `jtype: `)<br>        * the string literal of a JSON config<br><br>        When use it under Python, one can use the following values additionally:<br>        - a Python dict that represents the config<br>        - a text file stream has `.read()` interface | `string` | `BaseExecutor` |
| `uses_with` | Dictionary of keyword arguments that will override the `with` configuration in `uses` | `object` | `None` |
| `uses_metas` | Dictionary of keyword arguments that will override the `metas` configuration in `uses` | `object` | `None` |
| `uses_requests` | Dictionary of keyword arguments that will override the `requests` configuration in `uses` | `object` | `None` |
| `uses_dynamic_batching` | Dictionary of keyword arguments that will override the `dynamic_batching` configuration in `uses` | `object` | `None` |
| `py_modules` | The customized python modules need to be imported before loading the executor<br><br>Note that the recommended way is to only import a single module - a simple python file, if your<br>executor can be defined in a single file, or an ``__init__.py`` file if you have multiple files,<br>which should be structured as a python package. For more details, please see the<br>`Executor cookbook <https://docs.jina.ai/concepts/executor/executor-files/>`__ | `array` | `None` |
| `output_array_type` | The type of array `tensor` and `embedding` will be serialized to.<br><br>Supports the same types as `docarray.to_protobuf(.., ndarray_type=...)`, which can be found <br>`here <https://docarray.jina.ai/fundamentals/document/serialization/#from-to-protobuf>`.<br>Defaults to retaining whatever type is returned by the Executor. | `string` | `None` |
| `exit_on_exceptions` | List of exceptions that will cause the Executor to shut down. | `array` | `[]` |
| `no_reduce` | Disable the built-in reduction mechanism. Set this if the reduction is to be handled by the Executor itself by operating on a `docs_matrix` or `docs_map` | `boolean` | `False` |
| `grpc_server_options` | Dictionary of kwargs arguments that will be passed to the grpc server as options when starting the server, example : {'grpc.max_send_message_length': -1} | `object` | `None` |
| `entrypoint` | The entrypoint command overrides the ENTRYPOINT in Docker image. when not set then the Docker image ENTRYPOINT takes effective. | `string` | `None` |
| `docker_kwargs` | Dictionary of kwargs arguments that will be passed to Docker SDK when starting the docker '<br>container. <br><br>More details can be found in the Docker SDK docs:  https://docker-py.readthedocs.io/en/stable/ | `object` | `None` |
| `volumes` | The path on the host to be mounted inside the container. <br><br>Note, <br>- If separated by `:`, then the first part will be considered as the local host path and the second part is the path in the container system. <br>- If no split provided, then the basename of that directory will be mounted into container's root path, e.g. `--volumes="/user/test/my-workspace"` will be mounted into `/my-workspace` inside the container. <br>- All volumes are mounted with read-write mode. | `array` | `None` |
| `gpus` | This argument allows dockerized Jina Executors to discover local gpu devices.<br>    <br>    Note, <br>    - To access all gpus, use `--gpus all`.<br>    - To access multiple gpus, e.g. make use of 2 gpus, use `--gpus 2`.<br>    - To access specified gpus based on device id, use `--gpus device=[YOUR-GPU-DEVICE-ID]`<br>    - To access specified gpus based on multiple device id, use `--gpus device=[YOUR-GPU-DEVICE-ID1],device=[YOUR-GPU-DEVICE-ID2]`<br>    - To specify more parameters, use `--gpus device=[YOUR-GPU-DEVICE-ID],runtime=nvidia,capabilities=display | `string` | `None` |
| `disable_auto_volume` | Do not automatically mount a volume for dockerized Executors. | `boolean` | `False` |
| `host` | The host of the Gateway, which the client should connect to, by default it is 0.0.0.0. In the case of an external Executor (`--external` or `external=True`) this can be a list of hosts.  Then, every resulting address will be considered as one replica of the Executor. | `array` | `['0.0.0.0']` |
| `runtime_cls` | The runtime class to run inside the Pod | `string` | `WorkerRuntime` |
| `timeout_ready` | The timeout in milliseconds of a Pod waits for the runtime to be ready, -1 for waiting forever | `number` | `600000` |
| `env` | The map of environment variables that are available inside runtime | `object` | `None` |
| `env_from_secret` | The map of environment variables that are read from kubernetes cluster secrets | `object` | `None` |
| `floating` | If set, the current Pod/Deployment can not be further chained, and the next `.add()` will chain after the last Pod/Deployment not this current one. | `boolean` | `False` |
| `reload` | If set, the Executor will restart while serving if YAML configuration source or Executor modules are changed. If YAML configuration is changed, the whole deployment is reloaded and new processes will be restarted. If only Python modules of the Executor have changed, they will be reloaded to the interpreter without restarting process. | `boolean` | `False` |
| `install_requirements` | If set, try to install `requirements.txt` from the local Executor if exists in the Executor folder. If using Hub, install `requirements.txt` in the Hub Executor bundle to local. | `boolean` | `False` |
| `port` | The port for input data to bind to, default is a random port between [49152, 65535]. In the case of an external Executor (`--external` or `external=True`) this can be a list of ports. Then, every resulting address will be considered as one replica of the Executor. | `number` | `random in [49152, 65535]` |
| `monitoring` | If set, spawn an http server with a prometheus endpoint to expose metrics | `boolean` | `False` |
| `port_monitoring` | The port on which the prometheus server is exposed, default is a random port between [49152, 65535] | `number` | `random in [49152, 65535]` |
| `retries` | Number of retries per gRPC call. If <0 it defaults to max(3, num_replicas) | `number` | `-1` |
| `tracing` | If set, the sdk implementation of the OpenTelemetry tracer will be available and will be enabled for automatic tracing of requests and customer span creation. Otherwise a no-op implementation will be provided. | `boolean` | `False` |
| `traces_exporter_host` | If tracing is enabled, this hostname will be used to configure the trace exporter agent. | `string` | `None` |
| `traces_exporter_port` | If tracing is enabled, this port will be used to configure the trace exporter agent. | `number` | `None` |
| `metrics` | If set, the sdk implementation of the OpenTelemetry metrics will be available for default monitoring and custom measurements. Otherwise a no-op implementation will be provided. | `boolean` | `False` |
| `metrics_exporter_host` | If tracing is enabled, this hostname will be used to configure the metrics exporter agent. | `string` | `None` |
| `metrics_exporter_port` | If tracing is enabled, this port will be used to configure the metrics exporter agent. | `number` | `None` |
| `force_update` | If set, always pull the latest Hub Executor bundle even it exists on local | `boolean` | `False` |
| `prefer_platform` | The preferred target Docker platform. (e.g. "linux/amd64", "linux/arm64") | `string` | `None` |
| `compression` | The compression mechanism used when sending requests from the Head to the WorkerRuntimes. For more details, check https://grpc.github.io/grpc/python/grpc.html#compression. | `string` | `None` |
| `uses_before_address` | The address of the uses-before runtime | `string` | `None` |
| `uses_after_address` | The address of the uses-before runtime | `string` | `None` |
| `connection_list` | dictionary JSON with a list of connections to configure | `string` | `None` |
| `timeout_send` | The timeout in milliseconds used when sending data requests to Executors, -1 means no timeout, disabled by default | `number` | `None` |