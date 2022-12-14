(client)=
# Client
{class}`~jina.Client` enables you to send Documents to a running {class}`~jina.Flow`. Same as Gateway, Client supports four networking protocols: **gRPC**, **HTTP**, **WebSocket** and **GraphQL** with/without TLS.

You may have observed two styles of using a Client in the docs:

````{tab} Implicit, inside a Flow

```{code-block} python
---
emphasize-lines: 6
---
from jina import Flow

f = Flow()

with f:
    f.post('/')
```

````

````{tab} Explicit, outside a Flow

```{code-block} python
---
emphasize-lines: 3,4
---
from jina import Client

c = Client(...)  # must match the Flow setup
c.post('/')
```

````

The implicit style is easier in debugging and local development, as you don't need to specify the host, port and protocol of the Flow. However, it makes very strong assumptions on (1) one Flow only corresponds to one client (2) the Flow is running on the same machine as the Client. For those reasons, explicit style is recommended for production use.

```{hint}
If you want to connect to your Flow from a programming language other than Python, please follow the third party 
client {ref}`documentation <third-party-client>`.
```


## Connect

To connect to a Flow started by:

```python
from jina import Flow

with Flow(port=1234, protocol='grpc') as f:
    f.block()
```

```text
────────────────────────── 🎉 Flow is ready to serve! ──────────────────────────
╭────────────── 🔗 Endpoint ───────────────╮
│  ⛓      Protocol                   GRPC  │
│  🏠        Local           0.0.0.0:1234  │
│  🔒      Private     192.168.1.126:1234  │
│  🌍       Public    87.191.159.105:1234  │
╰──────────────────────────────────────────╯
```

The Client has to specify the followings parameters to match the Flow and how it was set up:
* the `protocol` it needs to use to communicate with the Flow
* the `host` and the `port` as exposed by the Flow
* if it needs to use `TLS` encryption (to connect to a {class}`~jina.Flow` that has been {ref}`configured to use TLS <flow-tls>` in combination with gRPC, http, or websocket)

    
````{Hint} Default port
The default port for the Client is `80` unless you are using `TLS` encryption it will be `443`
````


You can define these parameters by passing a valid URI scheme as part of the `host` argument:

````{tab} TLS disabled

```python
from jina import Client

Client(host='http://my.awesome.flow:1234')
Client(host='ws://my.awesome.flow:1234')
Client(host='grpc://my.awesome.flow:1234')
```

````

````{tab} TLS enabled

```python
from jina import Client

Client(host='https://my.awesome.flow:1234')
Client(host='wss://my.awesome.flow:1234')
Client(host='grpcs://my.awesome.flow:1234')
```

````


Equivalently, you can pass each relevant parameter as a keyword argument:

````{tab} TLS disabled

```python
from jina import Client

Client(host='my.awesome.flow', port=1234, protocol='http')
Client(host='my.awesome.flow', port=1234, protocol='websocket')
Client(host='my.awesome.flow', port=1234, protocol='grpc')
```

````

````{tab} TLS enabled

```python
from jina import Client

Client(host='my.awesome.flow', port=1234, protocol='http', tls=True)
Client(host='my.awesome.flow', port=1234, protocol='websocket', tls=True)
Client(host='my.awesome.flow', port=1234, protocol='grpc', tls=True)
```

````


You can also use a mix of both:

```python
from jina import Client

Client(host='https://my.awesome.flow', port=1234)
Client(host='my.awesome.flow:1234', protocol='http', tls=True)
```

````{admonition} Caution
:class: caution
You can't define these parameters both by keyword argument and by host scheme - you can't have two sources of truth.
Example: the following code will raise an exception:
```python
from jina import Client

Client(host='https://my.awesome.flow:1234', port=4321)
```
````

````{admonition} Caution
:class: caution
In case you instanciate a `Client` object using the `grpc` protocol, keep in mind that `grpc` clients cannot be used in 
a multi-threaded environment (check [this gRPC issue](https://github.com/grpc/grpc/issues/25364) for reference).
What you should do, is to rely on asynchronous programming or multi-processing rather than multi-threading.
For instance, if you're building a web server, you can introduce multi-processing based parallelism to your app using 
`gunicorn`: `gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker ...`
````



(client-compress)=
## Enable compression

If the communication to the Gateway is via gRPC, you can pass `compression` parameter to  {meth}`~jina.clients.mixin.PostMixin.post` to benefit from [gRPC compression](https://grpc.github.io/grpc/python/grpc.html#compression) methods. 

The supported choices are: None, `gzip` and `deflate`.

```python
from jina import Client

client = Client()
client.post(..., compression='Gzip')
```

Note that this setting is only effective the communication between the client and the Flow's gateway.

One can also specify the compression of the internal communication {ref}`as described here<server-compress>`.



## Test readiness of the Flow

```{include} ../flow/readiness.md
:start-after: <!-- start flow-ready -->
:end-before: <!-- end flow-ready -->
```

## Simple profiling of the latency

Before sending any real data, you can test the connectivity and network latency by calling the {meth}`~jina.Client.profiling` method:

```python
from jina import Client

c = Client(host='grpc://my.awesome.flow:1234')
c.profiling()
```

```text
 Roundtrip  24ms  100% 
├──  Client-server network  17ms  71% 
└──  Server  7ms  29% 
    ├──  Gateway-executors network  0ms  0% 
    ├──  executor0  5ms  71% 
    └──  executor1  2ms  29% 
```

```{toctree}
:hidden:

send-receive-data
send-parameters
send-graphql-mutation
callbacks
instrumentation
third-party-clients
```