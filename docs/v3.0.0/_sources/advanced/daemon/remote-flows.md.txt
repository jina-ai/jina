# Remote Flow

JinaD enables management of (remote + containerized) Flows with all your dependencies via REST APIs.

## Create Flow (<a href="https://api.jina.ai/daemon/#operation/_create_flows_post">redoc</a>)

This creates a new container using the base image, connects it to the network defined by `workspace_id` and starts a
Flow inside the container. Only the ports needed for external communication are mapped to local. Make sure you've added
all your config files while creating the workspace in the previous step.

```python
from daemon.clients import JinaDClient

client = JinaDClient(host=HOST, port=PORT)
client.flows.create(workspace_id=workspace_id, filename='my_awesome_flow.yml')
# jflow-a71cc28f-a5db-4cc0-bb9e-bb7797172cc9
```

## Get details of Flow (<a href="https://api.jina.ai/daemon/#operation/_status_flows__id__get">redoc</a>)

```python
client.flows.get(flow_id)
```

```json
{
  "time_created": "2021-07-27T05:12:06.646809",
  "metadata": {
    "container_id": "8770817435",
    "container_name": "jflow-a71cc28f-a5db-4cc0-bb9e-bb7797172cc9",
    "image_id": "28bd40a87e",
    "network": "6363b4a5b8",
    "ports": {
      "23456/tcp": 23456,
      "51567/tcp": 51567
    },
    "uri": "http://host.docker.internal:51567"
  },
  "arguments": {
    "object": {
      "time_created": "2021-07-27T05:12:06.640236",
      "arguments": {
        "port_expose": 23456,
        "name": None,
        "workspace": "./",
        "log_config": "/usr/local/lib/python3.7/site-packages/jina/resources/logging.default.yml",
        "quiet": False,
        "quiet_error": False,
        "workspace_id": "9db7a919-dfa5-420c-834e-ab940a40cbf2",
        "uses": None,
        "env": None,
        "inspect": 2
      },
      "yaml_source": "jtype: Flow\nversion: "1.0"\nwith:\n  protocol: http\n  port_expose: 23456\nexecutors:\n  - name: executor_ex\n"
    },
    "command": "--port-expose 51567 --mode flow --workspace-id 4d0a0db5-2cb8-4e8f-8183-966681c1c863"
  },
  "workspace_id": "jworkspace-4d0a0db5-2cb8-4e8f-8183-966681c1c863"
}
```

## Terminate Flow (<a href="https://api.jina.ai/daemon/#operation/_delete_flows__id__delete">redoc</a>)

```python
assert client.flows.delete(flow_id)
```
