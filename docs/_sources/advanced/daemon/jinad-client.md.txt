# JinaD Client

You can use `JinaDClient` or (for your async
code) feel free to use `AsyncJinaDClient` which makes all following code awaitables.

## Check if remote server is alive

```python
from daemon.clients import JinaDClient

client = JinaDClient(host=HOST, port=PORT)
assert client.alive
```

or,

```python
from daemon.clients import AsyncJinaDClient

client = AsyncJinaDClient(host=HOST, port=PORT)
assert await client.alive
```

## Get the status of the remote server

```python
from daemon.clients import JinaDClient

client = JinaDClient(host=HOST, port=PORT)
client.status
```

```json
{
  "jina" {
    "jina": "2.1.2",
    ...
  },
  "envs": {
    ...
  },
  "workspaces": {
    ...
  },
  "peas": {
    ...
  },
  "pods": {
    ...
  }
  "flows": {
    ...
  }
}
```
