(custom-gateway)=
# Customize the Gateway
A Jina Gateway is customizable and can be implemented in the same way Executors are implemented.
With Custom Gateways, Jina gives power back to the users, by allowing to implement any server, protocol and interface on
the gateway level. This means you have more freedom in:
* Choosing your favourite server framework.
* Choosing the protocol used to serve your app.
* Defining your API Gateway interface. You can define your JSON schema or protos,...

Customization is allowed different components:
* Implementing the custom gateway using a `base` gateway class: {class}`~jina.Gateway` or {class}`~jina.serve.runtimes.gateway.http.fastapi.FastAPIBaseGateway`.
* Using the {class}`~jina.serve.streamer.GatewayStreamer` to send data to Executors in the Flow.
* Implementing the needed health-checks for the runtime.
* Optionally, define a `config.yml` for it.
* Optionally, bootstrapping the gateway using a `Dockerfile` and re-using the docker image.

## Implementing the custom gateway
Similarly to how you would implement an Executor, you can implement a custom gateway by inheriting from a base gateway class.
Jina Gateway Runtime will instantiate your implemented class, inject runtime arguments and user-defined arguments to it, 
run it, send health-checks to it and orchestrate it.

Two Base Gateway classes are provided to allow implementing a custom gateway:
* {class}`~jina.Gateway`: Use this abstract class to implement a custom gateway of any type.
* {class}`~jina.serve.runtimes.gateway.http.fastapi.FastAPIBaseGateway`: Use this abstract class to implement a custom gateway using FastAPI.


### Using {class}`~jina.Gateway`:
To implement a custom gateway class using {class}`~jina.Gateway` do the following:
* Create a class that inherits from {class}`~jina.Gateway`
* Implement a constructor `__init__`:
This step is optional. You don't need a constructor if your Gateway doesn’t contain initial states. 
If your Gateway has `__init__`, it needs to carry `**kwargs` in the signature and call `super().__init__(**kwargs)` in the body:
```python
from jina import Gateway


class MyGateway(Gateway):
    def __init__(self, foo: str, **kwargs):
        super().__init__(**kwargs)
        self.foo = foo
```

* Implement `async def setup_server():`. This should set up a server runnable on an asyncio loop (and other resources 
needed for setting up the server). For instance:
```python
from jina import Gateway
from fastapi import FastAPI
from uvicorn import Server, Config


class MyGateway(Gateway):
    async def setup_server(self):
        app = FastAPI(title='My Custom Gateway')

        @app.get(path='/')
        def custom_endpoint():
            return {'message': 'custom-gateway'}

        self.server = Server(Config(app, host=self.host, port=self.port))
```
* Implement `async def run_server():`. This should run the server and await for it while serving:
```python
from jina import Gateway


class MyGateway(Gateway):
    ...

    async def run_server(self):
        await self.server.serve()
```
* Implement `async def shutdown():`. This should run the server and await for it while serving:
```python
from jina import Gateway


class MyGateway(Gateway):
    ...

    async def shutdown(self):
        self.server.should_exit = True
        await self.server.shutdown()
```

As an example, you can refer to {class}`~jina.serve.runtimes.gateway.grpc.GRPCGateway` and 
{class}`~jina.serve.runtimes.gateway.websocket.WebSocketGateway`.

### Using {class}`~jina.serve.runtimes.gateway.http.fastapi.FastAPIBaseGateway`:
{class}`~jina.serve.runtimes.gateway.http.fastapi.FastAPIBaseGateway` offers a simpler API to implement custom 
gateways but is restricted to FastAPI apps.

In order to implement a custom gateway using {class}`~jina.jina.serve.runtimes.gateway.http.fastapi.FastAPIBaseGateway`, 
simply implement the {meth}`~jina.jina.serve.runtimes.gateway.http.fastapi.FastAPIBaseGateway.app` property:

```python
from jina.serve.runtimes.gateway.http.fastapi import FastAPIBaseGateway


class DummyFastAPIGateway(FastAPIBaseGateway):
    @property
    def app(self):
        from fastapi import FastAPI

        app = FastAPI(title='Custom FastAPI Gateway')

        @app.get(path='/')
        def custom_endpoint():
            return {'message': 'custom-fastapi-gateway'}

        return app
```

As an example, you can refer to {class}`~jina.serve.runtimes.gateway.http.HTTPGateway`.

{class}`~jina.serve.runtimes.gateway.http.fastapi.FastAPIBaseGateway` is a subclass of {class}`~jina.Gateway` and therefore 
shares its attributes.

## Gateway arguments
### Runtime attributes
The runtime injects some attributes into the Gateway classes. You can use the to setup your custom gateway:
* name: gateway pod name.
* logger: Jina logger object.
* tracing: whether runtime tracing is enabled or not.
* tracer_provider: OpenTelemetry `TraceProvider` object.
* streamer: {class}`~jina.serve.streamer.GatewayStreamer`. Use this object to send Documents from the Gateway to Executors. Refer to {ref}`this section <gateway-streamer>` for more information.
* runtime_args: `argparse.Namespace` object containing runtime arguments.
* port: main port exposed by the Gateway.
* ports: list all ports exposed by the Gateway.
* protocols: list all protocols supported by the Gateway.
* host: host address to which the Gateway server should be bound.

```{admonition} Nonte
:class: note

The runtime provides the Gateway with a list of ports and protocols to expose. Therefore, a Custom Gateway can serve on 
multiple ports and protocols.
```

### User-defined parameters
Users can add other parameters by implementing a constructor `__init__`. Parameters of the constructor can be set and 
overridden in the Flow Python API (using `uses_with` parameter) or in the YAML configuration when including the gateway.
Refer to the {ref}`Use Custom Gateway section <use-custom-gateway>` for more information.

(gateway-streamer)=
## Calling Executors with {class}`~jina.serve.streamer.GatewayStreamer`
{class}`~jina.serve.streamer.GatewayStreamer` allows you to interface with Executors within the gateway. An instance of 
this class knows about the Flow structure and contains a connection pool to connect to each executor. You can get this 
object in 2 different ways:
* A `streamer` object (instance of {class}`~jina.serve.streamer.GatewayStreamer`) is injected by the runtime to your gateway class.
* In case your server logic cannot access the Gateway class (for instance separate script), you can still get a stream 
object using {meth}`~jina.serve.streamer.get_streamer()`.

After transforming requests that arrive to the gateway server into Documents, you can send them to Executors in the Flow 
using {meth}`~jina.serve.streamer.GatewayStreamer.stream_docs` :
```python
from jina.serve.runtimes.gateway.http.fastapi import FastAPIBaseGateway
from jina import Document, DocumentArray
from fastapi import FastAPI


class MyGateway(FastAPIBaseGateway):
    @property
    def app(self):
        app = FastAPI()

        @app.get("/")
        def get(text: str):
            result = None
            async for docs in self.streamer.stream_docs(
                docs=DocumentArray([Document(text=text)]),
                exec_endpoint='/',
            ):
                result = docs[0].text
            return {'result': result}
```


## Required health-checks
Jina relies on performing health-checks to determine the health of the gateway. In environments like kubernetes, 
docker-compose and Jina Cloud, this information is crucial to restart the gateway in case of failure.
Since the user has the full power over custom gateways, he always has the responsibility of implementing health-check 
endpoints:
* If the protocol used is GRPC, a health servicer (for instance `health.aio.HealthServicer()`) from `grpcio-health-checking` 
is expected to be added to the gRPC server. Refer to {class}`~jina.serve.runtimes.gateway.grpc.gateway.GRPCGateway` as 
an example.
* Otherwise, an HTTP GET request to the root path is expected to return a 200 status code.

To test whether your server properly implements health-checks, you can use the command `jina ping <protocol>://host:port`

```{admonition} Important
:class: important

Although a Jina Gateway can expose multiple ports and protocols, the runtime only cares about the first exposed port 
and protocol. Health checks will be sent only to the first port.
```
## Gateway YAML file
Like Executor `config` files, a Custom Gateway implementation can be associated with a YAML configuration file.
Such a configuration can override user-defined parameters and define other runtime arguments (port, protocol, py_modules,...).

For instance, you can define such a configuration in `config.yml`:
```yaml
!MyCustomGateway
py_modules: custom_gateway.py
with:
  arg1: hello
  arg2: world
port: 12345
```

For more information, please refer to the {ref}`Gateway YAML Specifications <gateway-yaml-spec>`
## Containerize the Custom Gateway
You may want to dockerize your Custom Gateway so you can isolate its dependencies and make it ready to run in the cloud 
or Kubernetes.

This assumes that you've already implemented a Custom Gateway class and have defined a `config.yml` for it.
In this case, dockerizing the gateway should be straighforward:
* If you need dependencies other than Jina, make sure to add a `requirements.txt` file (for instance, you use a server library).
* Create a `Dockerfile` which should have the following components:
1. Use a [Jina based image](https://hub.docker.com/r/jinaai/jina) as the base image in your Dockerfile.
This ensures that everything needed for Jina to run the Gateway is installed. Make sure the Jina Version used supports 
Custom Gateways:
```dockerfile
FROM jinaai/jina:3.12.0-py37-perf
```
Alternatively, you can just install jina using `pip`:
```dockerfile
RUN pip install jina
```

2. Install `requirements.txt`
3. Use the `jina gateway --uses config.yml` command as your image's entrypoint:
```dockerfile
ENTRYPOINT ["jina", "gateway", "--uses", "config.yml"]
```

Once you finish the `Dockerfile` you should end up with the following file structure:
```
.
├── my_gateway.py
└── requirements.txt
└── config.yml
└── Dockerfile
```
(use-custom-gateway)=
## Use the Custom Gateway
You can include the Custom Gateway in a jina Flow in different formats: Python class, configuration YAML and docker image:

`````{tab} Flow python API
````{tab} Python Class
```python
from jina import Gateway, Flow


class MyHTTPGateway(Gateway):
    def __init__(self, arg: str = None, **kwargs):
        super().__init__(**kwargs)
        self.arg = arg

    ...


flow = Flow().config_gateway(
    uses=MyHTTPGateway, port=12345, protocol='http', uses_with={'arg': 'value'}
)
```
````

````{tab} YAML configuration
```python
flow = Flow().config_gateway(
    uses='config.yml', port=12345, protocol='http', uses_with={'arg': 'value'}
)
```
````

````{tab} Docker Image
```python
flow = Flow().config_gateway(
    uses='docker://gateway-image',
    port=12345,
    protocol='http',
    uses_with={'arg': 'value'},
)
```
````
`````

`````{tab} Flow YAML configuration
````{tab} Python Class
```yaml
!Flow
gateway:
  py_modules: gateway.py
  uses: MyHTTPGateway
  with:
    arg: value
  protocol: http
  port: 12344
```
````

````{tab} YAML configuration
```yaml
!Flow
gateway:
  uses: gateway-config.yml
  protocol: http
  port: 12344
```
````

````{tab} Docker Image
```yaml
!Flow
gateway:
  uses: docker://gateway-image
  protocol: http
  port: 12344
```
````
`````

```{admonition} Important
:class: important

When you include a custom gateway in a Jina Flow, since the runtime needs to know about the port and protocol to which 
health checks will be sent, it is important to specify them when including the gateway.
```
