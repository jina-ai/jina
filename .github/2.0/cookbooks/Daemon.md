<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
Table of Contents

- [JinaD (Daemon)](#jinad-daemon)
  - [Server](#server)
      - [Run](#run)
      - [API Docs](#api-docs)
  - [Client (Python)](#client-python)
  - [Workspace](#workspace)
  - [RESTful Executors](#restful-executors)
  - [RESTful Flows](#restful-flows)
  - [Logstreaming](#logstreaming)
  - [Development using JinaD](#development-using-jinad)
      - [Build](#build)
      - [Run](#run-1)
      - [Why?](#why)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# JinaD (Daemon)

JinaD is a [daemon](https://en.wikipedia.org/wiki/Daemon_(computing)) for deploying and managing Jina on remote via a RESTful interface. It allows users to create/update/delete Flows and Executors on remote hosts. It achieves isolation of deployments by defining a `workspace` for each Jina object, hence allowing a multi-tenant setup with parallel Flows on the same host.

------

## Server

`JinaD` docker image is published on [Docker Hub](https://hub.docker.com/r/jinaai/jina/tags?page=1&ordering=last_updated&name=-daemon) and follows the [standard image versioning](https://github.com/jina-ai/jina/blob/master/RELEASE.md#docker-image-versioning) used in Jina.

#### Run

To deploy JinaD, SSH into a remote instance (e.g.- ec2 instance) and run the below command.

```bash
docker run --add-host host.docker.internal:host-gateway \
           -v /var/run/docker.sock:/var/run/docker.sock \
           -v /tmp/jinad:/tmp/jinad \
           -p 8000:8000 \
           --name jinad \
           -d jinaai/jina:master-daemon
```

<details>
<summary><strong>Points to note</strong></summary>

- You can change the port via the `-p` argument. Following code assumes that `HOST` is the public IP of the above instance and `PORT` is as passed in the docker run cpmmand.

- `JinaD` should always be deployed as a docker container. Simply starting the server using `jinad` command would not work.

</details>

#### API Docs

- [Static docs with redoc](https://api.jina.ai/daemon/)

- [Interactive swagger docs](http://localhost:8000/docs) (works once JinaD is started)

## Client (Python)

With `v2.0.12`, we introduce a Python Client to work with JinaD servers. You can use `JinaDClient` or (for your async code) feel free to use `AsyncJinaDClient` which makes all following code awaitables.

<details>
<summary><strong>Check if remote is alive</strong></summary>

<!-- #### Connect from local -->

```python
from daemon.clients import JinaDClient
client = JinaDClient(host=HOST, port=PORT)
assert client.alive

# OR,
from daemon.clients import AsyncJinaDClient
client = AsyncJinaDClient(host=HOST, port=PORT)
assert await client.alive
```

</details>

<details>
<summary><strong>Get remote status</strong></summary>

```python
from daemon.clients import JinaDClient
client = JinaDClient(host=HOST, port=PORT)
client.status
```

<details>
<summary>Example response</summary>

```text
{
  'jina' {
    'jina': '2.0.11',
    ...
  },
  'envs': {
    ...
  },
  'workspaces': {
    ...
  },
  'peas': {
    ...
  },
  'pods': {
    ...
  }
  'flows': {
    ...
  }
}
```

</details>
</details>

------

## Workspace

<details>
<summary><strong>What is a workspace?</strong></summary>

Workspace is the entrypoint for all objects in JinaD. It primarily represents 3 things.

1. **Docker Image**

    All objects created by JinaD are containerized. Workspace is responsible for building the base image. You can customize each image with the help of a `.jinad` file and a `requirements.txt` file.

2. **Docker Network**

    Workspace is also responsible for managing a private `bridge` network for all child containers. This provides network isolation from other workspaces, while allowing all containers inside the same workspace to communicate.

3. **Local work directory**

    All the files used to manage a Jina object or created by a Jina object are stored here. This directory is exposed to all child containers. These can be:
     - config files (e.g.- Flow/Executor YAML, Python modules etc),
     - data written by your Executor
     - logs (created by `fluentd`)
     - `.jinad` file
     - `requirements.txt` file

4. **Special files**

   - `.jinad` is an optional file defining how the base image is built. Following arguments are supported.

     ```ini
     build = default                 ; NOTE: devel/default, (gpu: to be added).
     python = 3.7                    ; NOTE: 3.7, 3.8, 3.9 allowed.
     jina = 2.0.rc7                  ; NOTE: to be added.
     ports = 45678                   ; NOTE: comma separated ports to be mapped.
     run = "python app.py 45678"     ; NOTE: command to start a Jina project on remote.
     ```

     You can also deploy an end-to-end Jina project on remote using the following steps.
     - Include a `.jinad` file with `run` set to your default entrypoint (e.g. - `python app.py`)
     - Upload all your files including `.jinad` during workspace creation.
     - This will deploy a custom container with your project

   - `requirements.txt` defines all python packages to be installed using `pip` in the base image.

     ```text
     annoy
     torch>=1.8.0
     tensorflow
     ```

</details>

<details>
<summary><strong>Create a workspace (<a href="https://api.jina.ai/daemon/#operation/_create_workspaces_post">redoc</a>)</strong></summary>

Create a directory (say `awesome_project`) on local which has all your files (`yaml`, `py_modules`, `requirements.txt`, `.jinad` etc.)

```python
from daemon.clients import JinaDClient
client = JinaDClient(host=HOST, port=PORT)
my_workspace_id = client.workspaces.create(paths=['path_to_awesome_project'])
```

<details>
<summary>Example response</summary>

  ```text

     JinaDClient@16018[I]:uploading 3 file(s): flow.yml, requirements.txt, .jinad
  🌏 36f9d7f70145 DaemonWorker1 INFO  ---> 70578df55b1c
  🌏 36f9d7f70145 DaemonWorker1 INFO Step 4/7 : ARG PIP_REQUIREMENTS
  🌏 36f9d7f70145 DaemonWorker1 INFO  ---> Running in e1588f87b32c
  🌏 36f9d7f70145 DaemonWorker1 INFO Removing intermediate container e1588f87b32c
  🌏 36f9d7f70145 DaemonWorker1 INFO  ---> 9f715ea59f8a
  🌏 36f9d7f70145 DaemonWorker1 INFO Step 5/7 : RUN if [ -n "$PIP_REQUIREMENTS" ]; then         echo "Installing
  ${PIP_REQUIREMENTS}";         for package in ${PIP_REQUIREMENTS}; do             pip install "${package}";         done;     fi
  🌏 36f9d7f70145 DaemonWorker1 INFO  ---> Running in e9018896b366
  🌏 36f9d7f70145 DaemonWorker1 INFO Installing tinydb sklearn
  🌏 36f9d7f70145 DaemonWorker1 INFO Collecting tinydb
  🌏 36f9d7f70145 DaemonWorker1 INFO   Downloading tinydb-4.5.1-py3-none-any.whl (23 kB)
  🌏 36f9d7f70145 DaemonWorker1 INFO Requirement already satisfied: typing-extensions<4.0.0,>=3.10.0 in
  /usr/local/lib/python3.7/site-packages (from tinydb) (3.10.0.0)
  🌏 36f9d7f70145 DaemonWorker1 INFO Installing collected packages: tinydb
  🌏 36f9d7f70145 DaemonWorker1 INFO Successfully installed tinydb-4.5.1
  🌏 36f9d7f70145 DaemonWorker1 WARNING WARNING: Running pip as the 'root' user can result in broken permissions and conflicting
  behaviour with the system package manager. It is recommended to use a virtual environment instead:
  https://pip.pypa.io/warnings/venv
  🌏 36f9d7f70145 DaemonWorker1 INFO Collecting sklearn
  🌏 36f9d7f70145 DaemonWorker1 INFO   Downloading sklearn-0.0.tar.gz (1.1 kB)
  🌏 36f9d7f70145 DaemonWorker1 INFO Collecting scikit-learn
  🌏 36f9d7f70145 DaemonWorker1 INFO   Downloading scikit_learn-0.24.2-cp37-cp37m-manylinux2010_x86_64.whl (22.3 MB)
  🌏 36f9d7f70145 DaemonWorker1 INFO Collecting joblib>=0.11
  🌏 36f9d7f70145 DaemonWorker1 INFO   Downloading joblib-1.0.1-py3-none-any.whl (303 kB)
  🌏 36f9d7f70145 DaemonWorker1 INFO Requirement already satisfied: numpy>=1.13.3 in /usr/local/lib/python3.7/site-packages (from
  scikit-learn->sklearn) (1.21.1)
  🌏 36f9d7f70145 DaemonWorker1 INFO Collecting scipy>=0.19.1
  🌏 36f9d7f70145 DaemonWorker1 INFO   Downloading scipy-1.7.0-cp37-cp37m-manylinux_2_5_x86_64.manylinux1_x86_64.whl (28.5 MB)
  🌏 36f9d7f70145 DaemonWorker1 INFO Collecting threadpoolctl>=2.0.0
  🌏 36f9d7f70145 DaemonWorker1 INFO   Downloading threadpoolctl-2.2.0-py3-none-any.whl (12 kB)
  🌏 36f9d7f70145 DaemonWorker1 INFO Building wheels for collected packages: sklearn
  🌏 36f9d7f70145 DaemonWorker1 INFO   Building wheel for sklearn (setup.py): started
  🌏 36f9d7f70145 DaemonWorker1 INFO   Building wheel for sklearn (setup.py): finished with status 'done'
  🌏 36f9d7f70145 DaemonWorker1 INFO   Created wheel for sklearn: filename=sklearn-0.0-py2.py3-none-any.whl size=1309 sha256=ac85019415e0eeebf468e2f71c43d8ff9b78131eaaccce89e34bb5ba8a2473ca
  🌏 36f9d7f70145 DaemonWorker1 INFO Successfully built sklearn
  🌏 36f9d7f70145 DaemonWorker1 INFO Installing collected packages: threadpoolctl, scipy, joblib, scikit-learn, sklearn
  🌏 36f9d7f70145 DaemonWorker1 INFO Successfully installed joblib-1.0.1 scikit-learn-0.24.2 scipy-1.7.0 sklearn-0.0 threadpoolctl-2.2.0
  🌏 36f9d7f70145 DaemonWorker1 WARNING WARNING: Running pip as the 'root' user can result in broken permissions and conflicting behaviour with the system package manager. It is recommended to
  use a virtual environment instead: https://pip.pypa.io/warnings/venv
  🌎  Workspace: Creating...    JinaDClient@16018[I]:jworkspace-480ec0d8-ea02-4adb-8e02-04cd27962863 created successfully
  ```

</details>
</details>

<details>
<summary><strong>Get details of a workspace (<a href="https://api.jina.ai/daemon/#operation/_list_workspaces__id__get">redoc</a>)</strong></summary>

```python
from daemon.clients import JinaDClient
client = JinaDClient(host=HOST, port=PORT)
client.workspaces.get(my_workspace_id)
```

<details>
<summary>Example response</summary>

```text
{
  'time_created': '2021-07-26T17:31:29.326049',
  'state': 'ACTIVE',
  'metadata': {
    'image_id': '97b0cb4860',
    'image_name': 'jworkspace:480ec0d8-ea02-4adb-8e02-04cd27962863',
    'network': '8dcd21b98a',
    'workdir': '/tmp/jinad/jworkspace-480ec0d8-ea02-4adb-8e02-04cd27962863',
    'container_id': None,
    'managed_objects': []
  },
  'arguments': {
    'files': ['flow.yml', 'requirements.txt', '.jinad'],
    'jinad': {
      'build': 'default',
      'dockerfile': '/usr/local/lib/python3.7/site-packages/daemon/Dockerfiles/default.Dockerfile'
    },
    'requirements': 'tinydb sklearn'
  }
}
```

</details>
</details>

<details>
<summary><strong>List all workspaces (<a href="https://api.jina.ai/daemon/#operation/_get_items_workspaces_get">redoc</a>)</strong></summary>

```python
client.workspaces.list()
```

<details>
<summary>Example response</summary>

```text
{
  'jworkspace-2b017b8f-19af-4d78-9364-6404447d91ac': {
    ...
  },
  'jworkspace-8fec6449-2824-4913-9c06-3d0ec1314674': {
    ...
  },
  'jworkspace-41dbe23a-9ecd-4e84-8df2-8dd6295a55b4': {
    ...
  },
  'jworkspace-0cc90166-5ce2-4702-9d30-0ff8f3598a9f': {
    ...
  },
  'jworkspace-be53f490-549a-4335-831a-5fb13a1de754': {
    ...
  },
  'jworkspace-48319ab9-6c36-4e2d-b687-dd0ab498cb4f': {
    ...
  }
}
```

</details>
</details>

<details>
<summary><strong>Delete a workspace (<a href="https://api.jina.ai/daemon/#operation/_delete_workspaces__id__delete">redoc</a>)</strong></summary>

```python
assert client.workspaces.delete(id=workspace_id)
```

</details>

------

## RESTful Executors

You wouldn't need to create remote Executors directly yourself. You can use the below code by passing `host` and `port_expose` to an executor with a Flow. Internally it uses `JinaD` for remote management.

```python
from jina import Flow
f = Flow().add(uses='path-to-executor.yml',
               py_modules=['path-to-executor.py', 'path-to-other-python-files.py'],
               upload_files=['path-to-requirements.txt'], # required only if additional pip packages are to be installed
               host=f'{HOST}:{PORT}')

with f:
  f.post(...)

```

<details>
<summary>In case you want to create remote Executors manually, you can follow the (advanced) guidelines below.</summary>

<details>
<summary><strong>Get all accepted arguments (<a href="https://api.jina.ai/daemon/#operation/_fetch_pea_params_peas_arguments_get">redoc</a>)</strong></summary>

```python
# Learn about payload
from daemon.clients import JinaDClient
client = JinaDClient(host=HOST, port=PORT)

# Get arguments accepted by Peas
client.peas.arguments()

# Get arguments accepted by Pods
client.pods.arguments()
```

<details>
<summary>Example response</summary>

```text
{
    "name": {
        "title": "Name",
        "description": "\nThe name of this object.\n\nThis will be used in the following places:\n- how you refer to this object in Python/YAML/CLI\n- visualization\n- log message header\n- ...\n\nWhen not given, then the default naming strategy will apply.\n                    ",
        "type": "string"
    },
    ...
}
```

</details>
</details>

<details>
<summary><strong>Create a Pea/Pod (<a href="https://api.jina.ai/daemon/#operation/_create_peas_post">redoc</a>)</strong></summary>

```python
# To create a Pea
client.peas.create(workspace_id=workspace_id, payload=payload)
#'jpea-5493e6b1-a5c6-45e9-95e2-54b00e4e77b4'

# To create a Pod
client.pods.create(workspace_id=workspace_id, payload=payload)
# jpod-44f8aeac-726e-4381-b5ff-9ae01e217b6d
```

</details>

<details>
<summary><strong>Get details of a Pea/Pod (<a href="https://api.jina.ai/daemon/#operation/_status_peas__id__get">redoc</a>)</strong></summary>

```python
# Pea
client.peas.get(pea_id)

# Pod
client.pods.get(pod_id)
```

<details>
<summary>Example response</summary>

```text
{
  'time_created': '2021-07-27T05:53:36.512694',
  'metadata': {
    'container_id': '6041041351',
    'container_name': 'jpea-6b94b5f2-828c-49a8-98e8-cb4cac2b5807',
    'image_id': '28bd40a87e',
    'network': '73a9b7ce2f',
    'ports': {
      '49591/tcp': 49591,
      '59647/tcp': 59647,
      '56237/tcp': 56237,
      '37389/tcp': 37389
    },
    'uri': 'http://host.docker.internal:37389'
  },
  'arguments': {
    'object': {
      'time_created': '2021-07-27T05:53:36.502625',
      'arguments': {
        'name': 'my_pea',
        ...
      }
    },
    'command': '--port-expose 37389 --mode pea --workspace-id 4df83da5-e227-4ecd-baac-3a54cdf7a22a'
  },
  'workspace_id': 'jworkspace-4df83da5-e227-4ecd-baac-3a54cdf7a22a'
}
```

</details>
</details>

<details>
<summary><strong>Terminate a Pea/Pod (<a href="https://api.jina.ai/daemon/#operation/_delete_peas__id__delete">redoc</a>)</strong></summary>

```python
# Pea
assert client.peas.delete(pea_id)

# Pod
assert client.pods.delete(pod_id)
```

</details>
</details>

------

## RESTful Flows

JinaD enables management of (remote + containerized) Flows with all your dependencies via REST APIs.

<details>
<summary><strong>Create a Flow (<a href="https://api.jina.ai/daemon/#operation/_create_flows_post">redoc</a>)</strong></summary>

This creates a new container using the base image, connects it to the network defined by `workspace_id` and starts a Flow inside the container. Only the ports needed for external communication are mapped to local. Make sure you've added all your config files while creating the workspace in the previous step.

```python
from daemon.clients import JinaDClient
client = JinaDClient(host=HOST, port=PORT)
client.flows.create(workspace_id=workspace_id, filename='my_awesome_flow.yml')
# jflow-a71cc28f-a5db-4cc0-bb9e-bb7797172cc9
```

</details>

<details>
<summary><strong>Get details of a Flow (<a href="https://api.jina.ai/daemon/#operation/_status_flows__id__get">redoc</a>)</strong></summary>

```python
client.flows.get(flow_id)
```

<details>
<summary>Example response</summary>

```text
{
  'time_created': '2021-07-27T05:12:06.646809',
  'metadata': {
    'container_id': '8770817435',
    'container_name': 'jflow-a71cc28f-a5db-4cc0-bb9e-bb7797172cc9',
    'image_id': '28bd40a87e',
    'network': '6363b4a5b8',
    'ports': {
      '23456/tcp': 23456,
      '51567/tcp': 51567
    },
    'uri': 'http://host.docker.internal:51567'
  },
  'arguments': {
    'object': {
      'time_created': '2021-07-27T05:12:06.640236',
      'arguments': {
        'port_expose': 23456,
        'name': None,
        'workspace': './',
        'log_config': '/usr/local/lib/python3.7/site-packages/jina/resources/logging.default.yml',
        'quiet': False,
        'quiet_error': False,
        'workspace_id': '9db7a919-dfa5-420c-834e-ab940a40cbf2',
        'uses': None,
        'env': None,
        'inspect': 2
      },
      'yaml_source': "jtype: Flow\nversion: '1.0'\nwith:\n  protocol: http\n  port_expose: 23456\nexecutors:\n  - name: executor_ex\n"
    },
    'command': '--port-expose 51567 --mode flow --workspace-id 4d0a0db5-2cb8-4e8f-8183-966681c1c863'
  },
  'workspace_id': 'jworkspace-4d0a0db5-2cb8-4e8f-8183-966681c1c863'
}
```

</details>
</details>

<details>
<summary><strong>Terminate a Flow (<a href="https://api.jina.ai/daemon/#operation/_delete_flows__id__delete">redoc</a>)</strong></summary>

```python
assert client.flows.delete(flow_id)
```

</details>

------

## Logstreaming

<details>
<summary>We can stream logs from a JinaD server for a running Flow/Pea/Pod/Workspace.</summary>

Unlike other modules, this needs to be awaited.

```python
from daemon.clients import AsyncJinaDClient
client = AsyncJinaDClient(host=HOST, port=PORT)
await client.logs(id=my_workspace_id)
```

<details>
<summary>Example response</summary>

```text
🌏 2358d9ab978a DaemonWorker8 INFO Step 1/5 : ARG LOCALTAG=test
🌏 2358d9ab978a DaemonWorker8 INFO Step 2/5 : FROM jinaai/jina:$LOCALTAG-daemon
🌏 2358d9ab978a DaemonWorker8 INFO  ---> c7d3770bb8bf
🌏 2358d9ab978a DaemonWorker8 INFO Step 3/5 : ARG PIP_REQUIREMENTS
🌏 2358d9ab978a DaemonWorker8 INFO  ---> Using cache
🌏 2358d9ab978a DaemonWorker8 INFO  ---> fef3bbb778c9
🌏 2358d9ab978a DaemonWorker8 INFO Step 4/5 : RUN if [ -n "$PIP_REQUIREMENTS" ]; then         echo "Installing ${PIP_REQUIREMENTS}";         for package in ${PIP_REQUIREMENTS}; do             pip install "${package}";         done;     fi
🌏 2358d9ab978a DaemonWorker8 INFO  ---> Using cache
🌏 2358d9ab978a DaemonWorker8 INFO  ---> 30ad9229b620
🌏 2358d9ab978a DaemonWorker8 INFO Step 5/5 : WORKDIR /workspace
🌏 2358d9ab978a DaemonWorker8 INFO  ---> Using cache
🌏 2358d9ab978a DaemonWorker8 INFO  ---> ee1abbf16f0e
🌏 2358d9ab978a DaemonWorker8 INFO Successfully built ee1abbf16f0e
🌏 2358d9ab978a DaemonWorker8 INFO Successfully tagged jworkspace:13305e16-aa7b-4f58-b0e9-1f420eb8be8b
🌏 2358d9ab978a DaemonWorker8 Level SUCCESS workspace jworkspace-13305e16-aa7b-4f58-b0e9-1f420eb8be8b is updated
```

</details>
</details>

------

## Development using JinaD

<details>
<summary>Follow the guidelines below, if you're developing using JinaD </summary>

#### Build

```bash
docker build -f Dockerfiles/debianx.Dockerfile --build-arg PIP_TAG=daemon -t jinaai/jina:test-daemon .
```

#### Run

```bash
docker run --add-host host.docker.internal:host-gateway \
           --name jinad \
           -e JINA_DAEMON_BUILD=DEVEL \
           -e JINA_LOG_LEVEL=DEBUG \
           -v /var/run/docker.sock:/var/run/docker.sock \
           -v /tmp/jinad:/tmp/jinad \
           -p 8000:8000 \
           -d jinaai/jina:test-daemon
```

#### Why?

- `jinaai/jina:test-daemon` ?

  All images created by JinaD during local tests use image with this name (hard-coded).

- `--env JINA_DAEMON_BUILD=DEVEL` ?

  This makes sure default build for JinaD is `DEVEL`. This must be passed during development, CICD etc

- `--add-host` ?

  `DOCKERHOST = 'host.docker.internal'`

  JinaD itself always runs inside a container and creates all images/networks/containers on localhost. `DOCKERHOST` allows JinaD to communicate with other child containers. Must for linux. Not needed for Mac/WSL

- `-v /var/run/docker.sock:/var/run/docker.sock` ?

  Allows JinaD to talk to DOCKERHOST

- `-v /tmp/jinad:/tmp/jinad` ?

  This is the default root workspace for JinaD. This gets mounted internally to all child containers. If we don't mount this while starting, `/tmp/jinad` local to JinaD would get mounted to child containers, which is not accessible by DOCKERHOST

</details>
