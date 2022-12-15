(access-flow-api)=
# Access Flow API

Once you have {ref}`configured your Flow API <flow-api>` you can access it over the network.
There are multiple ways of doing this.

## Jina Client

```{admonition} See Also
:class: seealso

For a more detailed description of the Jina Client, see its dedicated {ref}`documentation page <client>`.
```

Jina offers a built-in client that supports gRPC, HTTP, and Websocket connections to a Flow.
Sending a request to a Flow is as simple as calling the `.post()` method:

````{tab} gRPC

```{code-block} python
from docarray import Document, DocumentArray
from jina import Client

# Flow exposed on host HOST and port PORT
c = Client(host=HOST, port=PORT)
response_docs = c.post(on='/search', inputs=DocumentArray())
```
````

````{tab} HTTP
```{code-block} python
from docarray import Document, DocumentArray
from jina import Client

# Flow exposed on host HOST and port PORT
c = Client(host=HOST, port=PORT, protocol='http')
response_docs = c.post(on='/search', inputs=DocumentArray())
```
````

````{tab} WebSocket

```{code-block} python
from docarray import Document, DocumentArray
from jina import Client

# Flow exposed on host HOST and port PORT
c = Client(host=HOST, port=PORT, protocol='websocket')
response_docs = c.post(on='/search', inputs=DocumentArray())
```
````

The Client also supports a number of additional features, such as batching requests, callback functions, asynchronous calls,
passing additional parameters, and {ref}`more <client>`.

## HTTP access

```{admonition} Available Protocols
:class: caution
Jina Flows can use one of three protocols: gRPC, HTTP, or Websocket. Only Flows that use HTTP can be accessed via the
methods described below.
```

Outside of using the Jina Client, various forms of sending HTTP requests are the most common way of interacting with a Flow.

You can always use `post` to interact with a Flow, using the `/post` HTTP endpoint.
Your HTTP request can include the following parameters:

- `execEndpoint` - required: Executor endpoint string to target, e.g. `"execEndpoint": "/index"`
- `data` - optional: List specifying the input Documents, e.g. `"data": [{"text": "hello"}, {"text": "world"}]`.
- `paramters` - optional: Dictionary of parameters to be sent to the Executors, e.g. `"parameters": {"param1": "hello world"}`
- `targetExecutor` - optional: String indicating an Executor to target. Default targets all Executors, e.g. `"targetExecutor": "MyExec"`

Instead of using the generic `/post` endpoint, you can directly use endpoints like `/index` or `/search`.
In this case your data request will be sent to the corresponding Executor endpoint, so the parameter `execEndpoint` does not need to be specified.

In any case, the response you receive will include `data` (and array of Documents), as well as the fields `routes`, `parameters`, and `header`.

```{admonition} See also: Flow REST API
:class: seealso
For a more detailed descripton of the REST API of a generic Flow, including the complete request body schema and request samples, see [here](https://api.jina.ai/rest/).

For a specific deployed Flow, you can get the same overview by accessing the `/redoc` endpoint.
```

(swagger-ui)=
### Use Swagger UI to send HTTP request

Flows provide a customized [Swagger UI](https://swagger.io/tools/swagger-ui/) which can be used to interact with the Flow
visually, through a web browser.

```{admonition} Available Protocols
:class: caution
Only Flows that have {ref}`cors <cors>` enabled expose a Swagger UI interface.
```

For a Flow that is exposed on port `PORT`, you can navigate to the Swagger UI via `http://localhost:PORT/docs`:

```{figure} ../../../.github/2.0/swagger-ui.png
:align: center
```
Here you can see all the endpoints that are exposed by the Flow, such as `/search` and `/index`.

To send a request, click on the endpoint you want to target, then on `try it out`.

Now you can enter your HTTP request, and send it by clicking on `Execute`.
You can again use the [REST HTTP request schema](https://api.jina.ai/rest/), but do not need to specify `execEndpoint`.

You should see the raw response, together with a visual representation of the returned Documents.

### Use HTTP client to send request

You can send data requests to a Flow via cURL, Postman, or any other HTTP client.

<details>
  <summary>cURL example</summary>

    ```console
    $ curl --request POST 'http://localhost:12345/post' --header 'Content-Type: application/json' -d '{"data": [{"text": "hello world"}],"execEndpoint": "/index"}'
    
    {
      "requestId": "e2978837-e5cb-45c6-a36d-588cf9b24309",
      "data": {
        "docs": [
          {
            "id": "84d9538e-f5be-11eb-8383-c7034ef3edd4",
            "granularity": 0,
            "adjacency": 0,
            "parentId": "",
            "text": "hello world",
            "chunks": [],
            "weight": 0.0,
            "matches": [],
            "mimeType": "",
            "tags": {
              "mimeType": "",
              "parentId": ""
            },
            "location": [],
            "offset": 0,
            "embedding": null,
            "scores": {},
            "modality": "",
            "evaluations": {}
          }
        ],
        "groundtruths": []
      },
      "header": {
        "execEndpoint": "/index",
        "targetPeapod": "",
        "noPropagate": false
      },
      "parameters": {},
      "routes": [
        {
          "pod": "gateway",
          "podId": "5742d5dd-43f1-451f-88e7-ece0588b7557",
          "startTime": "2021-08-05T07:26:58.636258+00:00",
          "endTime": "2021-08-05T07:26:58.636910+00:00",
          "status": null
        }
      ],
      "status": {
        "code": 0,
        "description": "",
        "exception": null
      }
    }
    ```

</details>

(flow-graphql)=
## GraphQL Interface

````{admonition} See Also
:class: seealso

This article does not serve as the introduction to GraphQL.
If you are not already familiar with GraphQL, we recommend you learn more about GraphQL from the official [GraphQL documentation](https://graphql.org/learn/).
You may also want to learn about [Strawberry](https://strawberry.rocks/), the library that powers Jina's GraphQL support.
````
Jina Flows that use the HTTP protocol provide a GraphQL API out of the box, which is located behind the '/graphql' endpoint.
GraphQL has the advantage of letting the user define their own response schema, which means that only the fields that are required
will be sent over the wire.
This is especially useful when the user does not need potentially large fields, like image tensors.

You can access the Flow from any GraphQL client, like for example, `sgqlc`.

```python
from sgqlc.endpoint.http import HTTPEndpoint

HOSTNAME, PORT = ...
endpoint = HTTPEndpoint(url=f'{HOSTNAME}:{PORT}/graphql')
mut = '''
        mutation {
            docs(data: {text: "abcd"}) { 
                id
                matches {
                    embedding
                }
            } 
        }
    '''
response = endpoint(mut)
```

### Mutations and arguments

The Flow GraphQL API exposes the mutation `docs`, which sends its inputs to the Flow's Executors,
just like HTTP `post` as described {ref}`above <http-interface>`.

A GraphQL mutation can take the following arguments:

- `execEndpoint` - required: String representing the Executor endpoint to target, e.g. `execEndpoint: "/search"`
- `data` - optional: List of Documents to be processed by the Executors, e.g. `data: [{text: "hello"}, {text: "world"}`
- `parameters` - optional: Dictionary of parameters to be passed to the Executors, e.g. `parameters: {"my_param": 3}`
- `targetExecutor` - optional: String representing name of the Executor to target, e.g `"targetExecutor: "MyExec"`

The GraphQL response can include all fields available on a DocumentArray.

````{admonition} See Also
:class: seealso

For more details on the GraphQL format of Document and DocumentArray, see the [documentation page](https://docarray.jina.ai/advanced/graphql-support/)
or the [developer reference](https://docarray.jina.ai/api/docarray.document.mixins.strawberry/).
````


### Fields

The available fields in the GraphQL API are defined by the [Document Strawberry type](https://docarray.jina.ai/advanced/graphql-support/?highlight=graphql).

Essentially, you can ask for any property of a Document, including `embedding`, `text`, `tensor`, `id`, `matches`, `tags`,
and more.

## See further

- {ref}`Access a Flow with the Client <client>`
- {ref}`Configure Flow API <flow>`
- [Flow REST API reference](https://api.jina.ai/rest/)