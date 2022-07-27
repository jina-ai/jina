(jina-env-vars)=
# Environment Variables

Jina uses a number of environment variables to determine different behaviours.

If you use containerized Executors (including {ref}`Kubernetes <kubernetes>` and {ref}`Docker Compose <docker-compose>`), you can pass separate environment variables to each Executor in the following way:


`````{tab} YAML

```yaml
jtype: Flow
version: '1'
with: {}
executors:
- name: executor0
  port: 49583
  env:
    JINA_LOG_LEVEL: DEBUG
    MYSECRET: ${{ ENV.MYSECRET }}
- name: executor1
  port: 62156
  env:
    JINA_LOG_LEVEL: INFO
    CUDA_VISIBLE_DEVICES: 1
```
`````
````{tab} Python

```python
from jina import Flow
import os

secret = os.environ['MYSECRET']
f = (
    Flow()
    .add(env={'JINA_LOG_LEVEL': 'DEBUG', 'MYSECRET': secret})
    .add(env={'JINA_LOG_LEVEL': 'INFO', 'CUDA_VISIBLE_DEVICES': 1})
)
f.save_config("envflow.yml")
```
````

```{admonition} See Also
:class: seealso
For more information about the environment variable syntax used in Jina YAML configurations, see {ref}`here <migration-env-var>`.
```

The following environment variables are used internally in Jina:

| Environment variable          | Description                                                                                                      |
|-------------------------------|------------------------------------------------------------------------------------------------------------------|
| `JINA_AUTH_TOKEN`               | If provided, `jina hub push` pushes this Executor to specific account                                          |
| `JINA_DEFAULT_HOST`             | The default host where the server is exposed                                                                   |
| `JINA_DEFAULT_TIMEOUT_CTRL`     | The default timeout time used by Flow to check the readiness of Executors                                      |
| `JINA_DEFAULT_WORKSPACE_BASE`   | The default workspace folder used by an Executor if none provided through arguments                            |
| `JINA_DEPLOYMENT_NAME`          | The name of the deployment, used by the Head Runtime in Kubernetes to connect to different deployments         |
| `JINA_DISABLE_UVLOOP`           | If set, Jina will not use uvloop event loop for concurrent execution                                           |
| `JINA_FULL_CLI`                 | If set, all the CLI options will be shown in help                                                              |
| `JINA_GATEWAY_IMAGE`            | Used when exporting a Flow to Kubernetes or docker-compose to override the default gateway image               |
| `JINA_GRPC_RECV_BYTES`          | Set by the grpc service to keep track of the received bytes                                                    |
| `JINA_GRPC_SEND_BYTES`          | Set by the grpc service to keep track of the sent bytes                                                        |
| `JINA_HUBBLE_REGISTRY`          | Set it to point to a different Jina Hub registry                                                               |
| `JINA_HUB_CACHE_DIR`            | The directory where hub will cache its executors inside JINA_HUB_ROOT                                          |
| `JINA_HUB_ROOT`                 | The base directory for HubIO to store and read files                                                           |
| `JINA_LOG_CONFIG`               | The configuration used for the logger                                                                          |
| `JINA_LOG_LEVEL`                | The logging level used: INFO, DEBUG, WARNING                                                                   |
| `JINA_LOG_NO_COLOR`             | If set, disables color from rich console                                                                       |
| `JINA_MP_START_METHOD`          | Sets the multiprocessing start method used by jina                                                             |
| `JINA_RANDOM_PORT_MAX`          | The max port number used when selecting random ports to apply for Executors or gateway                         |
| `JINA_RANDOM_PORT_MIN`          | The min port number used when selecting random ports to apply for Executors or gateway                         |
| `JINA_DISABLE_HEALTHCHECK_LOGS` | If set, disables the logs when processing health check requests                                                |
| `JINA_LOCKS_ROOT`               | The root folder where file locks for concurrent Executor initialization                                        |
| `JINA_OPTOUT_TELEMETRY`        | If set, disables telemetry                                                                                     |
