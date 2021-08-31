## Create Remote Executors

You can use the below code by passing `host`
and `port_expose` to an executor with a Flow. Internally it uses `JinaD` for remote management.

```python
from jina import Flow

f = Flow().add(uses='path-to-executor.yml',
               py_modules=['path-to-executor.py', 'path-to-other-python-files.py'],
               upload_files=['path-to-requirements.txt'],
               # required only if additional pip packages are to be installed
               host=f'{HOST}:{PORT}')

with f:
    ...
```

##### Get all accepted arguments

```python
# Learn about payload
from daemon.clients import JinaDClient

client = JinaDClient(host=HOST, port=PORT)

# Get arguments accepted by Peas
client.peas.arguments()

# Get arguments accepted by Pods
client.pods.arguments()
```

```json
{
    "name": {
        "title": "Name",
        "description": "\nThe name of this object.\n\nThis will be used in the following places:\n- how you refer to this object in Python/YAML/CLI\n- visualization\n- log message header\n- ...\n\nWhen not given, then the default naming strategy will apply.\n                    ",
        "type": "string"
    },
    ...
}
```

##### Create a Pea/Pod (<a href="https://api.jina.ai/daemon/#operation/_create_peas_post">redoc</a>)

```python
# To create a Pea
client.peas.create(workspace_id=workspace_id, payload=payload)
# 'jpea-5493e6b1-a5c6-45e9-95e2-54b00e4e77b4'

# To create a Pod
client.pods.create(workspace_id=workspace_id, payload=payload)
# jpod-44f8aeac-726e-4381-b5ff-9ae01e217b6d
```

##### Get details of a Pea/Pod (<a href="https://api.jina.ai/daemon/#operation/_status_peas__id__get">redoc</a>)

```python
# Pea
client.peas.get(pea_id)

# Pod
client.pods.get(pod_id)
```

```json
{
  "time_created": "2021-07-27T05:53:36.512694",
  "metadata": {
    "container_id": "6041041351",
    "container_name": "jpea-6b94b5f2-828c-49a8-98e8-cb4cac2b5807",
    "image_id": "28bd40a87e",
    "network": "73a9b7ce2f",
    "ports": {
      "49591/tcp": 49591,
      "59647/tcp": 59647,
      "56237/tcp": 56237,
      "37389/tcp": 37389
    },
    "uri": "http://host.docker.internal:37389"
  },
  "arguments": {
    "object": {
      "time_created": "2021-07-27T05:53:36.502625",
      "arguments": {
        "name": "my_pea",
        ...
      }
    },
    "command": "--port-expose 37389 --mode pea --workspace-id 4df83da5-e227-4ecd-baac-3a54cdf7a22a"
  },
  "workspace_id": "jworkspace-4df83da5-e227-4ecd-baac-3a54cdf7a22a"
}
```


##### Terminate a Pea/Pod (<a href="https://api.jina.ai/daemon/#operation/_delete_peas__id__delete">redoc</a>)

```python
# Pea
assert client.peas.delete(pea_id)

# Pod
assert client.pods.delete(pod_id)
```
