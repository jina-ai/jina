# JinaD 2.0

##### Build JinaD

(checkout `daemon-2.0` branch)

```bash
docker build -f Dockerfiles/debianx.Dockerfile -t jinaai/jina:test-daemon .
```

##### Run JinaD

```bash
docker run --add-host host.docker.internal:host-gateway \
    --name jinad -v /var/run/docker.sock:/var/run/docker.sock -v /tmp/jinad:/tmp/jinad \
    -p 8000:8000 -d jinaai/jina:test-daemon
```

#### Why?

- `jinaai/jina:test-daemon` ?

  All images created by JinaD during local tests use image with this name (hard-coded). Once 2.0 is released, it would be pulled from `docker hub` or a better naming would get used.

- `--add-host`?

  `DOCKERHOST = 'host.docker.internal'`
  
  JinaD itself always runs inside a container and creates all images/networks/containers on localhost. `DOCKERHOST` allows JinaD to communicate with other child containers. Must for linux. Not needed for Mac/WSL

- `-v /var/run/docker.sock:/var/run/docker.sock` ?

  Allows JinaD to talk to DOCKERHOST

- `-v /tmp/jinad:/tmp/jinad` ?

  This is the default root workspace for JinaD. This gets mounted internally to all child containers. If we don't mount this while starting, `/tmp/jinad` local to JinaD would get mounted to child containers, which is not accessible by DOCKERHOST

## User journey

#### POST /workspaces

- Upload any file (yaml, python modules etc)

- Docker network creation

- Docker build using `.jinad` & `requirements.txt` files

- Run a custom-container if a `run` command is provided in `.jinad` file

  > This is not added as a separate endpoint. If `run` command is not provided, we don't start the custom-container)

`.jinad` (Not mandatory)

```ini
build = devel (NOTE: this would be default once we have jinad-2.0 released)
python = 3.7 (NOTE: 3.7, 3.8, 3.9 allowed)
ports = 45678 (NOTE: comma separated ports)
run = "python app.py 45678"
```

`requirements.txt`

```text
tensorflow
annoy
```

Returns a `201` response in `PENDING` state. Use `GET /workspaces/{id}` to wait until it comes to `ACTIVE` state.

#### POST /flows, /pods, /peas

- Must pass `workspace_id` created above (used to get the workdir, docker network, image).

- Remote pea creation is a time-taking process now, as it involves workspace creation.

- No support to upload flow yaml file here (just mention filename)

- Validates/modifies host/ports according to config.

- Evaluates what ports to open in child containers.

- Starts a container with `jinad` (mini-jinad) & sends a `POST /flow, /pod, /pea` request.

- Adds metadata to local store. Communications for `DELETE` & `UPDATE` (not implemented completely) are via `mini-jinad`.

### Metaworks

- Every restart of `jinad` can read from locally serialized store, enabling it not to be alive during whole lifecycle of flow (to be added: validation)

- A custom id `DaemonID` to define jinad objects.

### Tests

- [Dependency management with remote Pods](https://github.com/jina-ai/jina/blob/daemon-2.0/tests/distributed/test_against_external_daemon/test_remote_workspaces.py#L49)

- [Jina custom project](https://github.com/jina-ai/jina/blob/daemon-2.0/tests/distributed/test_against_external_daemon/test_remote_workspaces.py#L90)
