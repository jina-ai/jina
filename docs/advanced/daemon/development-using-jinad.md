# JinaD Development Guides

## Build

```bash
docker build -f Dockerfiles/debianx.Dockerfile --build-arg PIP_TAG=daemon -t jinaai/jina:test-daemon .
```

## Run

```bash
docker run --add-host host.docker.internal:host-gateway \
           --name jinad \
           -e JINA_DAEMON_DOCKERFILE=DEVEL \
           -e JINA_LOG_LEVEL=DEBUG \
           -v /var/run/docker.sock:/var/run/docker.sock \
           -v /tmp/jinad:/tmp/jinad \
           -p 8000:8000 \
           -d jinaai/jina:test-daemon
```

## Why?

- `jinaai/jina:test-daemon` ?

  All images created by JinaD during local tests use image with this name (hard-coded).

- `--env JINA_DAEMON_DOCKERFILE=DEVEL` ?

  This makes sure default build for JinaD is `DEVEL`. This should be passed only during development, CICD etc and must not be used when using the official image.

- `--add-host` ?

  `DOCKERHOST = 'host.docker.internal'`

  JinaD itself always runs inside a container and creates all images/networks/containers on localhost. `DOCKERHOST`
  allows JinaD to communicate with other child containers. Must for linux. Not needed for Mac/WSL

- `-v /var/run/docker.sock:/var/run/docker.sock` ?

  Allows JinaD to talk to DOCKERHOST

- `-v /tmp/jinad:/tmp/jinad` ?

  This is the default root workspace for JinaD. This gets mounted internally to all child containers. If we don't mount
  this while starting, `/tmp/jinad` local to JinaD would get mounted to child containers, which is not accessible by
  DOCKERHOST.
