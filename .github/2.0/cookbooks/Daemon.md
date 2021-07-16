<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
Table of Contents

- [JinaD 2.0](#jinad-20)
  - [Concepts](#concepts)
    - [Workspace](#workspace)
    - [RESTful Flows](#restful-flows)
    - [RESTful Pods/Peas](#restful-podspeas)
  - [Using JinaD](#using-jinad)
    - [Run](#run)
    - [Example Usage](#example-usage)
    - [Development using JinaD](#development-using-jinad)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->

# JinaD 2.0

JinaD is a daemon for deploying & managing Jina on remote via a RESTful interface. It achieves isolation of deployments by defining a `workspace` for each Jina object.

------

## Concepts

### Workspace

Workspace is the entrypoint for all objects in JinaD. It primarily represents 3 things.

- **Docker Image**

  All objects created by JinaD are containerized. Workspace is responsible for building the base image. Each image is built with the help of a `.jinad` file & a `requirements.txt` file.

- **Docker Network**

  Workspace is also responsible for managing a private `bridge` network for all child containers. This provides network isolation from other workspaces, while allowing all containers inside the same workspace to communicate.

- **Local work directory**

  All the files used to manage a Jina object or created by a Jina object are stored here. This directory is exposed to all child containers. These can be:
  - config files (e.g.- Flow/Executor YAML, Python modules etc),
  - data written by your Executor
  - logs (created by `fluentd`)
  - `.jinad` file
  - `requirements.txt` file

Use **POST /workspaces** to create a workspace. Special files:

- `.jinad` is an optional file defining how the base image is built. Following arguments are supported.

  ```ini
  build = devel                   ; NOTE: devel/cpu/gpu (default will be cpu once we have jinad-2.0 released), gpu: to be added.
  python = 3.7                    ; NOTE: 3.7, 3.8, 3.9 allowed.
  jina = 2.0.rc7                  ; NOTE: to be added.
  ports = 45678                   ; NOTE: comma separated ports to be mapped.
  run = "python app.py 45678"     ; NOTE: command to start a Jina project on remote.
  ```

  You can also deploy an end-toend Jina project on remote using the following steps.
  - Include a `.jinad` file with `run` set to your default entrypoint (e.g. - `python app.py`)
  - Upload all your files including `.jinad` during workspace creation.
  - This will deploy a custom container with your project

- `requirements.txt` defines all python packages to be installed using `pip` in the base image.

  ```text
  annoy
  torch>=1.8.0
  tensorflow
  ```

> NOTE: Since workspace creation takes time, `POST /workspaces` returns a `workspace_id` response in `PENDING` state. Use `GET /workspaces/{id}` to check the status of workspace creation & wait until it comes to `ACTIVE` state.

### RESTful Flows

Use **POST /flows** to create a Flow. Accepts following query params:

- `workspace_id` created above.

- `filename` signifies name of the Flow yaml file. The file must already be uploaded to the workspace.

This creates a new container using the base image & network defined by `workspace_id` & starts a Flow inside the container. Only the ports needed for external communication are mapped to DOCKERHOST. Update operations inside containers are also possible (mini JinaD)

### RESTful Pods/Peas

Use **POST /pods** or **POST /peas** to create a Pod/Pea. Accepts following args:

- `workspace_id` created above (query param)

- json body with all pod/pea related args

This creates a new container using the base image & network defined by `workspace_id` & starts a Pod/Pea inside the container. Only the ports needed for external communication are mapped to DOCKERHOST. Update operations inside containers are also possible (mini JinaD).

You can also create remote Pods inside a Flow using Python. This internally creates isolated Pods on remote.

```python
from jina import Flow
f = Flow().add(host='cloud.jina.ai:8000')
with f:
  f.post(...)
```

------

## Using JinaD

`JinaD` docker image is published on [Docker Hub](https://hub.docker.com/r/jinaai/jina/tags?page=1&ordering=last_updated&name=-daemon) & follows the [standard image versioning](https://github.com/jina-ai/jina/blob/master/RELEASE.md#docker-image-versioning) used in Jina.

### Run

```bash
docker run --add-host host.docker.internal:host-gateway \
           -v /var/run/docker.sock:/var/run/docker.sock \
           -v /tmp/jinad:/tmp/jinad \
           -p 8000:8000 \
           --name jinad \
           -d jinaai/jina:latest-daemon
```

**Note** : `JinaD` should always be deployed as a docker container. Simply starting the server using `jinad` command would not work.

**API Docs**

- [Static docs with redoc](https://api.jina.ai/daemon/)

- [Interactive swagger docs](http://localhost:8000/docs) (works once JinaD is started)


### Example Usage

- [Remote Flows](https://github.com/jina-ai/jina/blob/master/tests/distributed/test_workspaces/test_remote_workspaces.py#L96)

- [Dependency management with remote Pods](https://github.com/jina-ai/jina/blob/master/tests/distributed/test_workspaces/test_remote_workspaces.py#L55)

- [Jina custom project using workspaces](https://github.com/jina-ai/jina/blob/master/tests/distributed/test_workspaces/test_remote_workspaces.py#L108)

------

### Development using JinaD

##### Build

```bash
docker build -f Dockerfiles/debianx.Dockerfile --build-arg PIP_TAG=daemon -t jinaai/jina:test-daemon .
```

##### Run

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

##### Why?

- `jinaai/jina:test-daemon` ?

  All images created by JinaD during local tests use image with this name (hard-coded). Once 2.0 is released, it would be pulled from `docker hub` or a better naming would get used.

- `--env JINA_DAEMON_BUILD=DEVEL` ?

  This makes sure default build for JinaD is `DEVEL`. This must be passed during development, CICD etc

- `--add-host` ?

  `DOCKERHOST = 'host.docker.internal'`

  JinaD itself always runs inside a container and creates all images/networks/containers on localhost. `DOCKERHOST` allows JinaD to communicate with other child containers. Must for linux. Not needed for Mac/WSL

- `-v /var/run/docker.sock:/var/run/docker.sock` ?

  Allows JinaD to talk to DOCKERHOST

- `-v /tmp/jinad:/tmp/jinad` ?

  This is the default root workspace for JinaD. This gets mounted internally to all child containers. If we don't mount this while starting, `/tmp/jinad` local to JinaD would get mounted to child containers, which is not accessible by DOCKERHOST

##### Metaworks

- Every restart of `JinaD` can read from locally serialized store, enabling it not to be alive during whole lifecycle of flow (to be added: validation)

- A custom id `DaemonID` to define jinad objects.
